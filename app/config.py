import os
from pathlib import Path

class Config:
    # Secret key for sessions (CHANGE THIS in production!)
    SECRET_KEY = "super-secret-key-change-this-before-going-live"

    # Database Configuration - Absolute path (more reliable)
    BASE_DIR = Path(__file__).resolve().parent.parent
    INSTANCE_DIR = BASE_DIR / "instance"
    
    # Create the instance folder if it doesn't exist
    INSTANCE_DIR.mkdir(exist_ok=True)
    
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{INSTANCE_DIR}/inventory.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False