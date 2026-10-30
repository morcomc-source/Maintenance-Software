import os
from pathlib import Path

class Config:
    # Secret key for sessions (CHANGE THIS later)
    SECRET_KEY = "super-secret-key-change-this-before-going-live"

    # Absolute path to a local SQLite file for VM testing only
    BASE_DIR = Path(__file__).resolve().parent.parent
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{BASE_DIR / 'instance' / 'inventory.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
