# MongoDB Serve MCP

A containerized MCP (Model Context Protocol) server for connecting to production MongoDB databases via SSH tunnel.

## Features

- 🐳 **Dockerized**: Runs in a secure container environment
- 🔒 **SSH Tunneling**: Secure connection through SSH bastion host
- 🍃 **MongoDB Support**: Full MongoDB query and admin capabilities
- 📊 **Rich Tools**: Database listing, collection stats, querying, and more
- 🔧 **Production Ready**: Proper logging, error handling, and monitoring

## Quick Start

1. **Set up credentials**:
   ```bash
   # Copy your SSH credentials
   echo "your_ssh_username" > secrets/ssh_username.txt
   echo "your_ssh_password" > secrets/ssh_password.txt
   
   # Copy your MongoDB credentials  
   echo "your_mongodb_username" > secrets/mongodb_username.txt
   echo "your_mongodb_password" > secrets/mongodb_password.txt
   ```

2. **Build and run**:
   ```bash
   docker-compose up --build
   ```

3. **Test connection**:
   ```bash
   curl -X POST http://localhost:8000/tools/connect
   ```

## Configuration

Edit `.env` file or set environment variables:

- `SSH_HOST`: SSH bastion host (default: normdisco11.inet.telenet.be)
- `MONGODB_HOST`: MongoDB server (default: mongodb-norm.prd.telenet-ops.be)
- `REPLICA_SET`: MongoDB replica set (default: prd.norm.rs01)
- `LOG_LEVEL`: Logging level (default: INFO)

## Available Tools

- `connect()`: Connect to MongoDB
- `list_databases()`: List all databases
- `list_collections(database_name)`: List collections in a database
- `query_collection(database_name, collection_name, query, limit)`: Query documents
- `get_collection_stats(database_name, collection_name)`: Get collection statistics
- `disconnect()`: Close all connections

## Docker Commands

```bash
# Build and start
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Rebuild
docker-compose build --no-cache
```

## Claude Desktop Integration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mongodb-production": {
      "transport": {
        "type": "sse",
        "url": "http://localhost:8000"
      }
    }
  }
}
```