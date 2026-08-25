"""Acumen Backup & Restore - Protect your knowledge, conversations, and settings."""

import shutil
import json
from datetime import datetime
from pathlib import Path
from acumen.core.config import DATA_DIR, PROJECT_ROOT
from acumen.core.logger import get_logger

logger = get_logger("acumen.tools.backup")

BACKUP_DIR = PROJECT_ROOT / "backups"
BACKUP_DIR.mkdir(exist_ok=True)

def create_backup(name=None):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = name or f"acumen_backup_{timestamp}"
    backup_path = BACKUP_DIR / backup_name
    try:
        shutil.copytree(DATA_DIR, backup_path, dirs_exist_ok=True)
        manifest = {
            "name": backup_name,
            "created": datetime.now().isoformat(),
            "contents": {},
        }
        for subdir in backup_path.iterdir():
            if subdir.is_dir():
                file_count = sum(1 for f in subdir.rglob("*") if f.is_file())
                manifest["contents"][subdir.name] = file_count
        total = sum(manifest["contents"].values())
        manifest["total_files"] = total
        (backup_path / "manifest.json").write_text(json.dumps(manifest, indent=2))
        size_mb = sum(f.stat().st_size for f in backup_path.rglob("*") if f.is_file()) / (1024*1024)
        logger.info(f"Backup created: {backup_name} ({total} files, {size_mb:.1f} MB)")
        return {"name": backup_name, "path": str(backup_path), "files": total, "size_mb": round(size_mb, 1)}
    except Exception as e:
        logger.warning(f"Backup failed: {e}")
        return {"error": str(e)}

def restore_backup(backup_name):
    backup_path = BACKUP_DIR / backup_name
    if not backup_path.exists():
        return {"error": f"Backup not found: {backup_name}"}
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pre_restore = BACKUP_DIR / f"pre_restore_{timestamp}"
        shutil.copytree(DATA_DIR, pre_restore, dirs_exist_ok=True)
        logger.info(f"Pre-restore backup saved: {pre_restore.name}")
        for item in backup_path.iterdir():
            if item.name == "manifest.json":
                continue
            dest = DATA_DIR / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)
        logger.info(f"Restored from backup: {backup_name}")
        return {"status": "restored", "from": backup_name, "safety_backup": pre_restore.name}
    except Exception as e:
        logger.warning(f"Restore failed: {e}")
        return {"error": str(e)}

def list_backups():
    backups = []
    for d in BACKUP_DIR.iterdir():
        if d.is_dir():
            manifest_path = d / "manifest.json"
            if manifest_path.exists():
                manifest = json.loads(manifest_path.read_text())
                size_mb = sum(f.stat().st_size for f in d.rglob("*") if f.is_file()) / (1024*1024)
                backups.append({
                    "name": manifest["name"],
                    "created": manifest["created"],
                    "files": manifest.get("total_files", 0),
                    "size_mb": round(size_mb, 1),
                })
    return sorted(backups, key=lambda b: b["created"], reverse=True)

def delete_backup(backup_name):
    backup_path = BACKUP_DIR / backup_name
    if not backup_path.exists():
        return {"error": f"Backup not found: {backup_name}"}
    shutil.rmtree(backup_path)
    logger.info(f"Backup deleted: {backup_name}")
    return {"status": "deleted", "name": backup_name}