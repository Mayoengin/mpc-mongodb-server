#!/usr/bin/env python3
"""MongoDB MCP Server - Connect to MongoDB via SSH tunnel"""
import os
import sys
import logging
import logging.handlers
import json
import threading
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import OperationFailure
from bson import ObjectId
from sshtunnel import SSHTunnelForwarder
from mcp.server.fastmcp import FastMCP

# === LOGGING CONFIGURATION ===
def setup_logging():
    """Configure logging with rotation."""
    log_dir = os.getenv('LOG_DIR', '/tmp/mcp-logs')
    os.makedirs(log_dir, exist_ok=True)

    log_level = os.getenv('LOG_LEVEL', 'WARNING').upper()
    log_file = os.path.join(log_dir, 'mongodb-mcp-server.log')

    # Rotating file handler (5MB per file, keep 2 files)
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=5*1024*1024, backupCount=2, encoding='utf-8'
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(funcName)s - %(message)s'
    ))

    # Console handler for errors
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.ERROR)
    console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    root_logger.handlers.clear()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Suppress noisy third-party loggers
    for lib in ['pymongo', 'sshtunnel', 'paramiko', 'urllib3']:
        logging.getLogger(lib).setLevel(logging.ERROR)

    return logging.getLogger("mongodb-mcp-server")

logger = setup_logging()

# Initialize MCP server
mcp = FastMCP("mongodb-replica")

# Global state
_mongo_client = None
_ssh_tunnel = None
_tunnel_lock = threading.Lock()

def get_secret(secret_name):
    """Read secret from file or environment variable."""
    secret_file = os.getenv(f"{secret_name}_FILE")
    if secret_file and os.path.exists(secret_file):
        try:
            with open(secret_file, 'r') as f:
                return f.read().strip()
        except Exception as e:
            logger.warning(f"Failed to read secret file {secret_file}: {e}")
    return os.getenv(secret_name)

# Connection configuration - Load from Docker secrets or environment variables for security
SSH_HOST = os.getenv("SSH_HOST", "normdisco11.inet.telenet.be")
SSH_PORT = int(os.getenv("SSH_PORT", "22"))
SSH_USERNAME = get_secret("SSH_USERNAME")
SSH_PASSWORD = get_secret("SSH_PASSWORD")
MONGODB_HOST = os.getenv("MONGODB_HOST", "mongodb-norm.uat.telenet-ops.be")
MONGODB_PORT = int(os.getenv("MONGODB_PORT", "27017"))
MONGODB_USERNAME = get_secret("MONGODB_USERNAME")
MONGODB_PASSWORD = get_secret("MONGODB_PASSWORD")
MONGODB_AUTH_DB = os.getenv("MONGODB_AUTH_DB", "admin")
REPLICA_SET = os.getenv("REPLICA_SET", "uat.norm.rs01")

# Connection limits to prevent resource exhaustion
MAX_POOL_SIZE = int(os.getenv("MAX_POOL_SIZE", "5"))
CONNECTION_TIMEOUT_MS = int(os.getenv("CONNECTION_TIMEOUT_MS", "10000"))
SERVER_SELECTION_TIMEOUT_MS = int(os.getenv("SERVER_SELECTION_TIMEOUT_MS", "10000"))

# Validate required credentials are provided
def validate_credentials():
    """Validate that all required credentials are provided via environment variables."""
    required_vars = {
        'SSH_USERNAME': SSH_USERNAME,
        'SSH_PASSWORD': SSH_PASSWORD,
        'MONGODB_USERNAME': MONGODB_USERNAME,
        'MONGODB_PASSWORD': MONGODB_PASSWORD
    }

    missing_vars = [var for var, value in required_vars.items() if not value]

    if missing_vars:
        error_msg = f"Missing required credentials: {', '.join(missing_vars)}\n"
        error_msg += "\nPlease ensure the following environment variables are set:\n"
        for var in missing_vars:
            error_msg += f"  - {var}_FILE (path to file containing {var.lower()})\n"
            error_msg += f"  - or {var} (direct value)\n"
        logger.error(f"Missing credentials: {', '.join(missing_vars)}")
        raise ValueError(error_msg)

    logger.info("All required credentials loaded successfully")

# === UTILITY FUNCTIONS ===

def serialize_bson(obj):
    """Convert BSON objects to JSON-serializable format."""
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: serialize_bson(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_bson(item) for item in obj]
    return obj

def safe_json_parse(query_str):
    """Safely parse JSON query string."""
    if not query_str.strip():
        return {}
    try:
        return json.loads(query_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON query: {e}")

def create_ssh_tunnel():
    """Create SSH tunnel to MongoDB server."""
    global _ssh_tunnel

    with _tunnel_lock:
        if _ssh_tunnel and _ssh_tunnel.is_active:
            return _ssh_tunnel.local_bind_port

        try:
            _ssh_tunnel = SSHTunnelForwarder(
                (SSH_HOST, SSH_PORT),
                ssh_username=SSH_USERNAME,
                ssh_password=SSH_PASSWORD,
                remote_bind_address=(MONGODB_HOST, MONGODB_PORT),
                local_bind_address=('127.0.0.1', 0),
                allow_agent=False,
                host_pkey_directories=[],
                set_keepalive=30.0,
                ssh_config_file=None,
                threaded=True,
                logger=None
            )
            _ssh_tunnel.start()
            logger.debug(f"SSH tunnel created on port {_ssh_tunnel.local_bind_port}")
            return _ssh_tunnel.local_bind_port
        except Exception as e:
            logger.error(f"SSH tunnel creation failed: {e}")
            raise

def close_ssh_tunnel():
    """Close SSH tunnel with proper cleanup."""
    global _ssh_tunnel
    
    with _tunnel_lock:
        if _ssh_tunnel:
            try:
                _ssh_tunnel.stop()
                _ssh_tunnel = None
                logger.debug("SSH tunnel closed")
            except Exception as e:
                logger.error(f"Error closing SSH tunnel: {e}")

# === MCP TOOLS ===

async def ensure_connected():
    """Ensure MongoDB connection is active, auto-connect if needed."""
    global _mongo_client
    if not _mongo_client:
        connect_result = await connect()
        if "Error" in connect_result:
            raise RuntimeError(f"Connection failed: {connect_result}")

@mcp.tool()
async def connect() -> str:
    """Connect to MongoDB via SSH tunnel."""
    global _mongo_client

    try:
        # Validate credentials
        validate_credentials()

        # Close existing connections
        if _mongo_client:
            _mongo_client.close()
        close_ssh_tunnel()

        # Create SSH tunnel
        local_port = create_ssh_tunnel()

        # Connect to MongoDB through tunnel
        # Note: directConnection=true bypasses replica set discovery
        connection_string = f"mongodb://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@localhost:{local_port}/?authSource={MONGODB_AUTH_DB}&directConnection=true"

        _mongo_client = MongoClient(
            connection_string,
            serverSelectionTimeoutMS=SERVER_SELECTION_TIMEOUT_MS,
            connectTimeoutMS=CONNECTION_TIMEOUT_MS,
            socketTimeoutMS=30000,
            maxPoolSize=MAX_POOL_SIZE
        )

        # Test connection
        _mongo_client.admin.command('ping')
        version = _mongo_client.server_info().get('version', 'unknown')

        logger.info(f"Connected to MongoDB {version}")
        return f"✓ Connected to MongoDB {version} via {MONGODB_HOST}:{MONGODB_PORT}"

    except ValueError as e:
        logger.error(f"Credential validation failed: {e}")
        return f"Connection Error: {e}"
    except Exception as e:
        logger.error(f"Connection failed: {e}", exc_info=True)
        close_ssh_tunnel()
        return f"Connection Error: {e}"

@mcp.tool()
async def list_databases() -> str:
    """List all available databases."""
    try:
        await ensure_connected()
        db_names = _mongo_client.list_database_names()
        
        result = "Available Databases:\n\n"
        for i, db_name in enumerate(db_names, 1):
            try:
                db = _mongo_client[db_name]
                collections = db.list_collection_names()
                collection_count = len(collections)
                result += f"{i}. {db_name} ({collection_count} collections)\n"
            except Exception:
                result += f"{i}. {db_name} (access restricted)\n"
        
        return result
    except Exception as e:
        logger.error(f"List databases error: {e}")
        return f"Error: {e}"

@mcp.tool()
async def list_collections(database: str = "") -> str:
    """List collections in a specified database."""
    if not database.strip():
        return "Error: Database name is required"

    try:
        await ensure_connected()
        db = _mongo_client[database]
        collections = db.list_collection_names()
        
        if not collections:
            return f"No collections found in database '{database}'"
        
        result = f"Collections in '{database}' database:\n\n"
        for i, collection_name in enumerate(collections, 1):
            try:
                coll = db[collection_name]
                doc_count = coll.estimated_document_count()
                result += f"{i}. {collection_name} (~{doc_count:,} documents)\n"
            except Exception:
                result += f"{i}. {collection_name} (count unavailable)\n"
        
        return result
    except Exception as e:
        logger.error(f"List collections error: {e}")
        return f"Error: {e}"

@mcp.tool()
async def count(database: str = "", collection: str = "", query: str = "{}") -> str:
    """Count documents in collections with optional query filters."""
    if not database.strip():
        return "Error: Database name is required"
    if not collection.strip():
        return "Error: Collection name is required"

    try:
        await ensure_connected()
        query_filter = safe_json_parse(query)
        
        db = _mongo_client[database]
        coll = db[collection]
        
        if query_filter:
            count_result = coll.count_documents(query_filter)
        else:
            count_result = coll.estimated_document_count()
        
        return f"""Document Count Results:

Database: {database}
Collection: {collection}
Query: {query if query.strip() != '{}' else 'No filter (all documents)'}
Count: {count_result:,} documents"""
        
    except ValueError as e:
        return f"Query Error: {e}"
    except OperationFailure as e:
        return f"MongoDB Error: {e}"
    except Exception as e:
        logger.error(f"Count error: {e}")
        return f"Error: {e}"

@mcp.tool()
async def find(database: str = "", collection: str = "", query: str = "{}", projection: str = "", sort: str = "", limit: str = "10") -> str:
    """Query documents from collections."""
    if not database.strip():
        return "Error: Database name is required"
    if not collection.strip():
        return "Error: Collection name is required"

    try:
        await ensure_connected()
        query_filter = safe_json_parse(query)
        
        projection_dict = None
        if projection.strip():
            projection_dict = safe_json_parse(projection)
        
        sort_criteria = None
        if sort.strip():
            sort_criteria = safe_json_parse(sort)
            if isinstance(sort_criteria, dict):
                sort_criteria = list(sort_criteria.items())
        
        limit_int = int(limit) if limit.strip() else 10
        limit_int = min(limit_int, 100)  # Cap at 100 documents
        
        db = _mongo_client[database]
        coll = db[collection]
        
        cursor = coll.find(query_filter, projection_dict)
        
        if sort_criteria:
            cursor = cursor.sort(sort_criteria)
        
        cursor = cursor.limit(limit_int)
        
        documents = []
        for doc in cursor:
            documents.append(serialize_bson(doc))
        
        result_info = f"""Query Results:

Database: {database}
Collection: {collection}
Query: {query if query.strip() != '{}' else 'No filter'}
Projection: {projection if projection.strip() else 'All fields'}
Sort: {sort if sort.strip() else 'Natural order'}
Limit: {limit_int}
Found: {len(documents)} documents

"""
        
        if documents:
            result_info += "Documents:\n"
            for i, doc in enumerate(documents, 1):
                result_info += f"\n--- Document {i} ---\n"
                result_info += json.dumps(doc, indent=2, default=str)
                result_info += "\n"
        else:
            result_info += "No documents found matching the query."
        
        return result_info
        
    except ValueError as e:
        return f"Parameter Error: {e}"
    except OperationFailure as e:
        return f"MongoDB Error: {e}"
    except Exception as e:
        logger.error(f"Find error: {e}")
        return f"Error: {e}"

@mcp.tool()
async def aggregate(database: str = "", collection: str = "", pipeline: str = "[]") -> str:
    """Execute aggregation pipelines."""
    if not database.strip():
        return "Error: Database name is required"
    if not collection.strip():
        return "Error: Collection name is required"

    try:
        await ensure_connected()
        pipeline_list = safe_json_parse(pipeline)
        
        if not isinstance(pipeline_list, list):
            return "Error: Pipeline must be a JSON array"
        
        db = _mongo_client[database]
        coll = db[collection]
        
        cursor = coll.aggregate(pipeline_list)
        results = []

        for doc in cursor:
            if len(results) >= 100:  # Cap at 100 results
                break
            results.append(serialize_bson(doc))
        
        result_info = f"""Aggregation Results:

Database: {database}
Collection: {collection}
Pipeline: {pipeline}
Results: {len(results)} documents

"""
        
        if results:
            result_info += "Results:\n"
            for i, doc in enumerate(results, 1):
                result_info += f"\n--- Result {i} ---\n"
                result_info += json.dumps(doc, indent=2, default=str)
                result_info += "\n"
        else:
            result_info += "No results returned from aggregation."
        
        return result_info
        
    except ValueError as e:
        return f"Pipeline Error: {e}"
    except OperationFailure as e:
        return f"MongoDB Error: {e}"
    except Exception as e:
        logger.error(f"Aggregation error: {e}")
        return f"Error: {e}"

# === SERVER STARTUP ===

if __name__ == "__main__":
    logger.info("Starting MongoDB MCP server...")
    try:
        mcp.run(transport='stdio')
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        close_ssh_tunnel()
        sys.exit(1)
    finally:
        close_ssh_tunnel()