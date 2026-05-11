import pathlib
import pytest

def test_file_versions_migration_exists():
    """Ensure the file_versions migration script is present."""
    migration_path = pathlib.Path(__file__).parents[2] / "backend" / "alembic" / "versions" / "0004_create_file_versions_table.py"
    assert migration_path.is_file(), f"Missing migration file: {migration_path}"
