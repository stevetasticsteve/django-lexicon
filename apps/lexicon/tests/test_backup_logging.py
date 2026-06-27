
import os
import pytest
import logging
from apps.lexicon import models
from apps.lexicon.tasks import backup_projects
from django.conf import settings

@pytest.mark.django_db
def test_backup_logging(tmp_path, monkeypatch):
    # Setup directories
    backup_root = tmp_path / "data" / "backups"
    backup_root.mkdir(parents=True)
    log_dir = tmp_path / "data" / "logs"
    log_dir.mkdir(parents=True)
    log_file = log_dir / "backups.log"
    
    # Mock settings and tasks
    monkeypatch.setattr("apps.lexicon.tasks.BACKUP_DIR", str(backup_root))
    
    # Configure a temporary logger for testing
    logger = logging.getLogger("lexicon.backup")
    handler = logging.FileHandler(str(log_file))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    try:
        # Create a project
        models.LexiconProject.objects.create(
            language_name="Test Lang",
            language_code="tst",
            version=1
        )
        
        # 1. First backup (should create)
        backup_projects()
        
        with open(log_file, "r") as f:
            content = f.read()
            assert "Starting project backups" in content
            assert "Created backup for tst" in content
            assert "Version: 1" in content
            assert "Project backups completed" in content
            
        # 2. Second backup (should skip)
        backup_projects()
        
        with open(log_file, "r") as f:
            content = f.read()
            assert "Backup not required for tst" in content
            assert "Current version 1 matches or is less than latest backup version 1" in content
            
    finally:
        logger.removeHandler(handler)
        handler.close()
