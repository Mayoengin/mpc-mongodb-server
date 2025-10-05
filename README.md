# MongoDB MCP Server

A containerized MCP (Model Context Protocol) server for secure MongoDB access via SSH tunnel.

## Quick Start

1. **Setup credentials**:
   ```bash
   echo "your_ssh_username" > secrets/ssh_username.txt
   echo "your_ssh_password" > secrets/ssh_password.txt
   echo "your_mongodb_username" > secrets/mongodb_username.txt
   echo "your_mongodb_password" > secrets/mongodb_password.txt
   ```

2. **Run with Docker**:
   ```bash
   docker-compose up --build
   ```

## Claude Desktop Integration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mongodb-production": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-v", "/path/to/mongodb-serve-mcp/secrets:/app/secrets:ro",
        "-v", "/path/to/mongodb-serve-mcp/logs:/app/logs",
        "--env", "SSH_HOST=your.ssh.host",
        "--env", "MONGODB_HOST=your.mongodb.host",
        "--env", "REPLICA_SET=your.replica.set",
        "--env", "MCP_TRANSPORT=stdio",
        "mongodb-serve-mcp-mongodb-mcp-server"
      ]
    }
  }
}
```

## Available Tools

- `connect()` - Connect to MongoDB
- `list_databases()` - List all databases  
- `list_collections(db)` - List collections
- `query_collection(db, collection, query, limit)` - Query documents
- `get_collection_stats(db, collection)` - Collection statistics
- `disconnect()` - Close connections