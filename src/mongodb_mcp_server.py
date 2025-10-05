#!/usr/bin/env python3
"""
MongoDB MCP Server - Docker Edition
A containerized MCP server for connecting to production MongoDB via SSH tunnel
"""

import os
import sys
import logging
import logging.handlers
import threading
from typing import Any, Dict, List, Optional
from datetime import datetime

import pymongo
from pymongo import MongoClient
from pymongo.errors import OperationFailure, ConnectionFailure
from bson import ObjectId
from sshtunnel import SSHTunnelForwarder
from mcp.server.fastmcp import FastMCP


# === LOGGING CONFIGURATION ===
def setup_logging() -> logging.Logger:
    """Configure comprehensive logging with rotation."""
    log_dir = os.getenv('LOG_DIR', '/app/logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_file = os.path.join(log_dir, 'mongodb-mcp-server.log')
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    simple_formatter = logging.Formatter('%(levelname)s: %(message)s')
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setFormatter(detailed_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(simple_formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    root_logger.handlers.clear()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Suppress noisy third-party loggers
    for lib in ['pymongo', 'sshtunnel', 'paramiko', 'urllib3']:
        logging.getLogger(lib).setLevel(logging.WARNING)
    
    return logging.getLogger("mongodb-mcp-server")


# === SAFE LOGGING FUNCTION ===
def safe_log(level: str, message: str):
    """Safely log a message without causing stream errors during shutdown."""
    try:
        getattr(logger, level.lower())(message)
    except (ValueError, OSError, AttributeError):
        # Fallback to stderr if logging fails (streams closed during shutdown)
        try:
            print(f"{level.upper()}: {message}", file=sys.stderr)
        except:
            # If even stderr fails, silently ignore
            pass


# === CONFIGURATION ===
def get_secret(secret_name: str) -> Optional[str]:
    """Read secret from file or environment variable."""
    secret_file = os.getenv(f"{secret_name}_FILE")
    if secret_file and os.path.exists(secret_file):
        try:
            with open(secret_file, 'r') as f:
                return f.read().strip()
        except Exception as e:
            logger.warning(f"Failed to read secret file {secret_file}: {e}")
    
    # Fallback to environment variable
    return os.getenv(secret_name)


# Initialize logger
logger = setup_logging()

# Configuration
SSH_HOST = os.getenv("SSH_HOST", "normdev11.inet.telenet.be")
SSH_PORT = int(os.getenv("SSH_PORT", "22"))
SSH_USERNAME = get_secret("SSH_USERNAME")
SSH_PASSWORD = get_secret("SSH_PASSWORD")

MONGODB_HOST = os.getenv("MONGODB_HOST", "mongodb-norm.int.telenet-ops.be")
MONGODB_PORT = int(os.getenv("MONGODB_PORT", "27017"))
MONGODB_USERNAME = get_secret("MONGODB_USERNAME")
MONGODB_PASSWORD = get_secret("MONGODB_PASSWORD")
MONGODB_AUTH_DB = os.getenv("MONGODB_AUTH_DB", "admin")
REPLICA_SET = os.getenv("REPLICA_SET", "int.norm.rs01")

MCP_SERVER_HOST = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
MCP_SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", "8000"))

# Log configuration (without sensitive data)
logger.info("=== MongoDB MCP Server Starting ===")
logger.info(f"SSH Host: {SSH_HOST}:{SSH_PORT}")
logger.info(f"SSH Username: {SSH_USERNAME}")
logger.info(f"MongoDB Host: {MONGODB_HOST}:{MONGODB_PORT}")
logger.info(f"MongoDB Auth DB: {MONGODB_AUTH_DB}")
logger.info(f"Replica Set: {REPLICA_SET}")
logger.info(f"MCP Server: {MCP_SERVER_HOST}:{MCP_SERVER_PORT}")


# === GLOBAL STATE ===
_ssh_tunnel: Optional[SSHTunnelForwarder] = None
_mongo_client: Optional[MongoClient] = None
_tunnel_lock = threading.Lock()


# === MCP SERVER SETUP ===
mcp = FastMCP("MongoDB Production Server")


# === HELPER FUNCTIONS ===
def serialize_bson(obj: Any) -> Any:
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


def create_ssh_tunnel() -> SSHTunnelForwarder:
    """Create and start SSH tunnel."""
    logger.info(f"Creating SSH tunnel to {SSH_HOST}:{SSH_PORT}")
    
    try:
        tunnel = SSHTunnelForwarder(
            (SSH_HOST, SSH_PORT),
            ssh_username=SSH_USERNAME,
            ssh_password=SSH_PASSWORD,
            remote_bind_address=(MONGODB_HOST, MONGODB_PORT),
            local_bind_address=('127.0.0.1', 0),  # Let system choose port
            allow_agent=False,
            host_pkey_directories=[],
            set_keepalive=30.0,
            ssh_config_file=None,
            threaded=True,
            logger=None
        )
        
        tunnel.start()
        logger.info(f"SSH tunnel established: localhost:{tunnel.local_bind_port} -> {MONGODB_HOST}:{MONGODB_PORT}")
        return tunnel
        
    except Exception as e:
        logger.error(f"Failed to create SSH tunnel: {e}")
        # Try to handle the DSSKey error specifically
        if "DSSKey" in str(e):
            logger.warning("DSSKey error detected, trying with minimal SSH key configuration")
            # Monkey-patch paramiko to remove DSSKey if it doesn't exist
            try:
                import paramiko
                if not hasattr(paramiko, 'DSSKey'):
                    # Create a dummy DSSKey class if it doesn't exist
                    class DummyDSSKey:
                        @classmethod
                        def from_private_key_file(cls, *args, **kwargs):
                            raise NotImplementedError("DSS keys are deprecated")
                        
                        @classmethod
                        def from_private_key(cls, *args, **kwargs):
                            raise NotImplementedError("DSS keys are deprecated")
                    
                    paramiko.DSSKey = DummyDSSKey
                    
                    # Retry tunnel creation
                    tunnel = SSHTunnelForwarder(
                        (SSH_HOST, SSH_PORT),
                        ssh_username=SSH_USERNAME,
                        ssh_password=SSH_PASSWORD,
                        remote_bind_address=(MONGODB_HOST, MONGODB_PORT),
                        local_bind_address=('127.0.0.1', 0),
                        logger=logger.getChild('ssh'),
                        ssh_config_file=None,
                        host_pkey_directories=[],
                        ssh_pkey=None,
                        allow_agent=False,
                        look_for_keys=False
                    )
                    
                    tunnel.start()
                    logger.info(f"SSH tunnel established: localhost:{tunnel.local_bind_port} -> {MONGODB_HOST}:{MONGODB_PORT}")
                    return tunnel
            except Exception as inner_e:
                logger.error(f"Failed to fix DSSKey issue: {inner_e}")
        
        raise


def ensure_connection() -> bool:
    """Ensure SSH tunnel and MongoDB connection are active."""
    global _ssh_tunnel, _mongo_client
    
    with _tunnel_lock:
        try:
            # Check if tunnel is active
            if _ssh_tunnel is None or not _ssh_tunnel.is_active:
                if _ssh_tunnel:
                    logger.warning("SSH tunnel is inactive, recreating...")
                    try:
                        _ssh_tunnel.stop()
                    except:
                        pass
                
                _ssh_tunnel = create_ssh_tunnel()
            
            # Check MongoDB connection
            if _mongo_client is None:
                local_port = _ssh_tunnel.local_bind_port
                # Try with directConnection first (for SSH tunnel), fallback to replica set if needed
                connection_string = (
                    f"mongodb://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@localhost:{local_port}/"
                    f"?authSource={MONGODB_AUTH_DB}&directConnection=true"
                )
                
                logger.info(f"Connecting to MongoDB via tunnel on port {local_port}")
                logger.info(f"Auth DB: {MONGODB_AUTH_DB}, Username: {MONGODB_USERNAME}")
                logger.info(f"Connection string: mongodb://{MONGODB_USERNAME}:***@localhost:{local_port}/?authSource={MONGODB_AUTH_DB}&directConnection=true")
                _mongo_client = MongoClient(connection_string, serverSelectionTimeoutMS=10000)
                
                # Test connection
                _mongo_client.admin.command('ping')
                logger.info("MongoDB connection established successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"Connection error: {e}")
            
            # Cleanup on failure
            if _mongo_client:
                try:
                    _mongo_client.close()
                except:
                    pass
                _mongo_client = None
            
            if _ssh_tunnel and _ssh_tunnel.is_active:
                try:
                    _ssh_tunnel.stop()
                except:
                    pass
                _ssh_tunnel = None
            
            return False


# === MCP TOOLS ===
@mcp.tool()
def connect() -> str:
    """Connect to the production MongoDB database via SSH tunnel."""
    logger.info("Connection requested")
    
    try:
        # First, check if we already have a working connection
        if _mongo_client is not None:
            try:
                # Test existing connection
                _mongo_client.admin.command('ping')
                server_info = _mongo_client.server_info()
                version = server_info.get('version', 'unknown')
                logger.info("Using existing connection")
                return f"✅ Already connected to MongoDB Production Server (version {version})"
            except Exception as ping_error:
                logger.warning(f"Existing connection failed ping test: {ping_error}")
                # Fall through to ensure_connection()
        
        # If no working connection, establish one
        success = ensure_connection()
        if success:
            # Get server info
            server_info = _mongo_client.server_info()
            version = server_info.get('version', 'unknown')
            return f"✅ Connected to MongoDB Production Server (version {version})"
        else:
            return "❌ Failed to connect to MongoDB Production Server"
    
    except Exception as e:
        error_msg = f"Connection Error: {str(e)}"
        # Include full error details for debugging
        if hasattr(e, 'details'):
            error_msg += f", full error: {e.details}"
        logger.error(error_msg)
        return error_msg


@mcp.tool()
def list_databases() -> str:
    """List all databases in the MongoDB instance."""
    logger.info("Listing databases")
    
    try:
        success = ensure_connection()
        if not success:
            return "❌ Not connected to MongoDB"
        
        databases = _mongo_client.list_database_names()
        db_count = len(databases)
        
        result = f"📊 Found {db_count} databases:\n"
        for i, db_name in enumerate(sorted(databases), 1):
            result += f"{i:2d}. {db_name}\n"
        
        logger.info(f"Listed {db_count} databases")
        return result
    
    except Exception as e:
        error_msg = f"Error listing databases: {str(e)}"
        logger.error(error_msg)
        return error_msg


@mcp.tool()
def list_collections(database_name: str) -> str:
    """List all collections in a specific database."""
    logger.info(f"Listing collections in database: {database_name}")
    
    try:
        success = ensure_connection()
        if not success:
            return "❌ Not connected to MongoDB"
        
        db = _mongo_client[database_name]
        collections = db.list_collection_names()
        coll_count = len(collections)
        
        result = f"📁 Database '{database_name}' contains {coll_count} collections:\n"
        for i, coll_name in enumerate(sorted(collections), 1):
            result += f"{i:2d}. {coll_name}\n"
        
        logger.info(f"Listed {coll_count} collections in {database_name}")
        return result
    
    except Exception as e:
        error_msg = f"Error listing collections: {str(e)}"
        logger.error(error_msg)
        return error_msg


@mcp.tool()
def query_collection(database_name: str, collection_name: str, query: str = '{}', limit: int = 10) -> str:
    """Query a collection with optional filter and limit."""
    logger.info(f"Querying {database_name}.{collection_name} with query: {query[:100]}...")
    
    try:
        success = ensure_connection()
        if not success:
            return "❌ Not connected to MongoDB"
        
        import json
        
        # Parse query
        try:
            query_dict = json.loads(query) if query.strip() else {}
        except json.JSONDecodeError as e:
            return f"❌ Invalid JSON query: {str(e)}"
        
        # Execute query
        collection = _mongo_client[database_name][collection_name]
        cursor = collection.find(query_dict).limit(limit)
        documents = list(cursor)
        
        if not documents:
            return f"📄 No documents found in {database_name}.{collection_name} matching query"
        
        # Serialize results
        serialized_docs = [serialize_bson(doc) for doc in documents]
        
        result = f"📄 Found {len(documents)} documents in {database_name}.{collection_name}:\n\n"
        for i, doc in enumerate(serialized_docs, 1):
            result += f"Document {i}:\n"
            result += json.dumps(doc, indent=2)
            result += "\n" + "="*50 + "\n"
        
        logger.info(f"Retrieved {len(documents)} documents from {database_name}.{collection_name}")
        return result
    
    except Exception as e:
        error_msg = f"Error querying collection: {str(e)}"
        logger.error(error_msg)
        return error_msg


@mcp.tool()
def get_collection_stats(database_name: str, collection_name: str) -> str:
    """Get statistics for a specific collection."""
    logger.info(f"Getting stats for {database_name}.{collection_name}")
    
    try:
        success = ensure_connection()
        if not success:
            return "❌ Not connected to MongoDB"
        
        collection = _mongo_client[database_name][collection_name]
        
        # Get basic stats
        count = collection.count_documents({})
        
        # Get collection stats from MongoDB
        try:
            stats = _mongo_client[database_name].command("collStats", collection_name)
            size_bytes = stats.get('size', 0)
            storage_size = stats.get('storageSize', 0)
            avg_obj_size = stats.get('avgObjSize', 0)
            index_count = stats.get('nindexes', 0)
        except:
            # Fallback if collStats fails
            size_bytes = storage_size = avg_obj_size = index_count = 0
        
        result = f"📊 Statistics for {database_name}.{collection_name}:\n"
        result += f"  • Document count: {count:,}\n"
        result += f"  • Data size: {size_bytes:,} bytes ({size_bytes/1024/1024:.2f} MB)\n"
        result += f"  • Storage size: {storage_size:,} bytes ({storage_size/1024/1024:.2f} MB)\n"
        result += f"  • Average document size: {avg_obj_size:.0f} bytes\n"
        result += f"  • Number of indexes: {index_count}\n"
        
        logger.info(f"Retrieved stats for {database_name}.{collection_name}")
        return result
    
    except Exception as e:
        error_msg = f"Error getting collection stats: {str(e)}"
        logger.error(error_msg)
        return error_msg


@mcp.tool()
def disconnect() -> str:
    """Disconnect from MongoDB and close SSH tunnel."""
    global _ssh_tunnel, _mongo_client
    
    safe_log("info", "Disconnect requested")
    
    try:
        with _tunnel_lock:
            # Close MongoDB client
            if _mongo_client:
                _mongo_client.close()
                _mongo_client = None
                safe_log("info", "MongoDB client closed")
            
            # Stop SSH tunnel
            if _ssh_tunnel and _ssh_tunnel.is_active:
                _ssh_tunnel.stop()
                _ssh_tunnel = None
                safe_log("info", "SSH tunnel closed")
        
        return "✅ Disconnected from MongoDB Production Server"
    
    except Exception as e:
        error_msg = f"Error during disconnect: {str(e)}"
        safe_log("error", error_msg)
        return error_msg


# === MAIN FUNCTION ===
def main():
    """Main entry point for the MCP server."""
    logger.info("Starting MongoDB MCP Server...")
    
    try:
        # Test initial connection
        logger.info("Testing initial connection...")
        success = ensure_connection()
        if success:
            logger.info("✅ Initial connection test successful")
        else:
            logger.warning("⚠️ Initial connection test failed, but server will continue")
            logger.warning("The MCP server will start but MongoDB operations may fail until connection is established")
        
        # Start the MCP server
        # Use TCP transport for Docker, stdio for direct usage
        transport_mode = os.getenv("MCP_TRANSPORT", "tcp")
        
        if transport_mode == "tcp":
            logger.info(f"Starting MCP server on TCP {MCP_SERVER_HOST}:{MCP_SERVER_PORT}")
            mcp.run(transport="tcp", host=MCP_SERVER_HOST, port=MCP_SERVER_PORT)
        else:
            logger.info("Starting MCP server on stdio")
            mcp.run(transport="stdio")
        
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    except Exception as e:
        safe_log("error", f"Server error: {e}")
        raise
    finally:
        # Cleanup - don't log if stdio is closed
        safe_log("info", "Cleaning up connections...")
        
        # Perform actual cleanup
        try:
            disconnect()
        except Exception as disconnect_error:
            safe_log("error", f"Disconnect error: {disconnect_error}")
        
        safe_log("info", "MongoDB MCP Server stopped")


if __name__ == "__main__":
    main()