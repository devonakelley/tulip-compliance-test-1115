#!/bin/bash
set -e

# Configuration
BACKUP_DIR="/app/backups"
DATE=$(date +"%Y%m%d_%H%M%S")
MONGO_BACKUP_DIR="$BACKUP_DIR/mongodb_$DATE"
APP_BACKUP_DIR="$BACKUP_DIR/application_$DATE"

echo "🗄️  Starting backup process..."

# Create backup directories
mkdir -p "$MONGO_BACKUP_DIR" "$APP_BACKUP_DIR"

# Backup MongoDB
echo "📊 Backing up MongoDB..."
if command -v mongodump &> /dev/null; then
    mongodump --uri="mongodb://localhost:27017" --db="qsp_compliance" --out="$MONGO_BACKUP_DIR"
    echo "✅ MongoDB backup completed: $MONGO_BACKUP_DIR"
else
    echo "⚠️  mongodump not found. Using Docker to backup..."
    docker exec qsp-mongodb mongodump --db=qsp_compliance --out=/data/backup
    docker cp qsp-mongodb:/data/backup "$MONGO_BACKUP_DIR/"
    echo "✅ MongoDB backup completed via Docker: $MONGO_BACKUP_DIR"
fi

# Backup application data
echo "📁 Backing up application data..."
cp -r uploads "$APP_BACKUP_DIR/" 2>/dev/null || echo "No uploads directory found"
cp -r processed "$APP_BACKUP_DIR/" 2>/dev/null || echo "No processed directory found"
cp -r logs "$APP_BACKUP_DIR/" 2>/dev/null || echo "No logs directory found"

# Create compressed archive
echo "🗜️  Compressing backup..."
tar -czf "$BACKUP_DIR/qsp_backup_$DATE.tar.gz" -C "$BACKUP_DIR" \
    "mongodb_$DATE" "application_$DATE"

# Clean up temporary directories
rm -rf "$MONGO_BACKUP_DIR" "$APP_BACKUP_DIR"

# Remove old backups (keep last 7 days)
echo "🧹 Cleaning old backups..."
find "$BACKUP_DIR" -name "qsp_backup_*.tar.gz" -mtime +7 -delete

echo "✅ Backup completed successfully!"
echo "📦 Backup file: $BACKUP_DIR/qsp_backup_$DATE.tar.gz"