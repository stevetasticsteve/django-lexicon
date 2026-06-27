import os
import json
import pytest
from django.core.management import call_command
from apps.lexicon import models
from apps.lexicon.tasks import backup_projects

@pytest.mark.django_db
def test_backup_projects_flow(tmp_path, monkeypatch):
    # Set up data/backups in a temp directory
    backup_root = tmp_path / "data" / "backups"
    backup_root.mkdir(parents=True)
    
    # Mock BACKUP_DIR in tasks.py
    monkeypatch.setattr("apps.lexicon.tasks.BACKUP_DIR", str(backup_root))
    
    # Create a project
    project = models.LexiconProject.objects.create(
        language_name="Test Lang",
        language_code="tst",
        version=1
    )
    
    # 1. Initial backup creation
    backup_projects()
    
    project_backup_dir = backup_root / "tst"
    assert project_backup_dir.exists()
    backups = sorted(list(project_backup_dir.glob("*.json")))
    assert len(backups) == 1
    
    # Verify backup content
    with open(backups[0], "r", encoding="utf-8") as f:
        data = json.load(f)
        assert data["project"]["version"] == 1
        assert data["project"]["language_code"] == "tst"

    # 2. Skip backup if version hasn't changed
    backup_projects()
    backups = sorted(list(project_backup_dir.glob("*.json")))
    assert len(backups) == 1

    # 3. Create new backup when version increases
    project.version = 2
    project.save()
    
    # The task uses filename with timestamp YYYY-MM-DD_HHMMSS
    # If we run too fast it might have same timestamp, but the logic 
    # should still work if we allow it, though the filename might collide 
    # if it's the exact same second.
    # In practice, it should be fine for tests if we just want to see it works.
    
    # Mocking datetime to ensure different timestamps if needed, 
    # but let's see if it works naturally first or just use a small sleep.
    import time
    time.sleep(1.1) 
    
    backup_projects()
    backups = sorted(list(project_backup_dir.glob("*.json")))
    assert len(backups) == 2
    
    # Verify latest backup content
    with open(backups[-1], "r", encoding="utf-8") as f:
        data = json.load(f)
        assert data["project"]["version"] == 2

@pytest.mark.django_db
def test_backup_projects_multiple_projects(tmp_path, monkeypatch):
    backup_root = tmp_path / "data" / "backups"
    backup_root.mkdir(parents=True)
    monkeypatch.setattr("apps.lexicon.tasks.BACKUP_DIR", str(backup_root))
    
    models.LexiconProject.objects.create(language_name="Lang1", language_code="l1", version=1)
    models.LexiconProject.objects.create(language_name="Lang2", language_code="l2", version=5)
    
    backup_projects()
    
    assert (backup_root / "l1").exists()
    assert (backup_root / "l2").exists()
    
    assert len(list((backup_root / "l1").glob("*.json"))) == 1
    assert len(list((backup_root / "l2").glob("*.json"))) == 1

@pytest.mark.django_db
def test_backup_projects_corrupt_backup_recovery(tmp_path, monkeypatch):
    backup_root = tmp_path / "data" / "backups"
    backup_root.mkdir(parents=True)
    monkeypatch.setattr("apps.lexicon.tasks.BACKUP_DIR", str(backup_root))
    
    project = models.LexiconProject.objects.create(language_name="Test", language_code="tst", version=2)
    
    # Create a corrupt backup file
    project_dir = backup_root / "tst"
    project_dir.mkdir()
    corrupt_file = project_dir / "tst_backup_2023-01-01_000000.json"
    corrupt_file.write_text("invalid json")
    
    # Should still create a new backup because it can't read the old one's version
    backup_projects()
    
    backups = list(project_dir.glob("*.json"))
    assert len(backups) == 2
    
    # One of them should be valid
    valid_backups = []
    for b in backups:
        try:
            with open(b, "r") as f:
                valid_backups.append(json.load(f))
        except:
            pass
    assert len(valid_backups) == 1
    assert valid_backups[0]["project"]["version"] == 2

@pytest.mark.django_db
def test_backup_projects_management_command(tmp_path, monkeypatch):
    backup_root = tmp_path / "data" / "backups"
    backup_root.mkdir(parents=True)
    monkeypatch.setattr("apps.lexicon.tasks.BACKUP_DIR", str(backup_root))
    
    models.LexiconProject.objects.create(language_name="Test", language_code="tst", version=1)
    
    # Run management command
    call_command("backup_projects")
    
    project_backup_dir = backup_root / "tst"
    assert project_backup_dir.exists()
    assert len(list(project_backup_dir.glob("*.json"))) == 1
