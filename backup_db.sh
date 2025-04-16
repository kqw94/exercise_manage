#!/bin/bash
# 配置
DB_USER="root"
DB_PASS="swt@Ddd963741000"
DB_NAME="exercise_db"
BACKUP_DIR="./backups/db"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/  backup_$DATE.sql.gz"

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 备份并压缩
mysqldump -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" | gzip > "$BACKUP_FILE"

# 删除 7 天前的备份
find "$BACKUP_DIR" -name "backup_*.sql.gz" -mtime +7 -delete

echo "Backup created: $BACKUP_FILE"