#!/bin/bash
set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 <backup_file.tar.gz>"
    echo "Available backups:"
    ls -la /app/backups/qsp_backup_*.tar.gz 2>/dev/null || echo "No backups found"
    exit 1
fi

BACKUP_FILE="$1"
BACKUP_DIR="/app/backups"
RESTORE_DIR="$BACKUP_DIR/restore_$(date +%s)"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "🔄 Starting restore process..."
echo "📦 Backup file: $BACKUP_FILE"

# Create restore directory
mkdir -p "$RESTORE_DIR"

# Extract backup
echo "📂 Extracting backup..."
tar -xzf "$BACKUP_FILE" -C "$RESTORE_DIR"

# Find MongoDB backup
MONGO_RESTORE=$(find "$RESTORE_DIR" -name "mongodb_*" -type d | head -1)
if [ -z "$MONGO_RESTORE" ]; then
    echo "❌ MongoDB backup not found in archive"
    exit 1
fi

# Find application backup
APP_RESTORE=$(find "$RESTORE_DIR" -name "application_*" -type d | head -1)

# Restore MongoDB
echo "📊 Restoring MongoDB..."
if command -v mongorestore &> /dev/null; then
    mongorestore --uri="mongodb://localhost:27017" --drop "$MONGO_RESTORE"
else
    echo "Using Docker to restore..."
    docker cp "$MONGO_RESTORE/." qsp-mongodb:/data/restore/
    docker exec qsp-mongodb mongorestore --db=qsp_compliance --drop /data/restore/qsp_compliance
fi
echo "✅ MongoDB restore completed"

# Restore application data
if [ -n "$APP_RESTORE" ]; then
    echo "📁 Restoring application data..."
    
    # Backup current data
    if [ -d "uploads" ]; then
        mv uploads "uploads.backup.$(date +%s)"
    fi
    if [ -d "processed" ]; then
        mv processed "processed.backup.$(date +%s)"
    fi
    
    # Restore data
    cp -r "$APP_RESTORE/uploads" . 2>/dev/null || echo "No uploads to restore"
    cp -r "$APP_RESTORE/processed" . 2>/dev/null || echo "No processed files to restore"
    
    echo "✅ Application data restore completed"
fi

# Clean up
rm -rf "$RESTORE_DIR"

echo "🎉 Restore completed successfully!"
echo "🔄 You may need to restart the application: docker-compose restart"