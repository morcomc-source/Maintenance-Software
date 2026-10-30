import os
from pathlib import Path

class Config:
    # Secret key for sessions (CHANGE THIS later)
    SECRET_KEY = "super-secret-key-change-this-before-going-live"

    # PostgreSQL Database
    SQLALCHEMY_DATABASE_URI = "postgresql://maintenance_user:Maintenance2026!@localhost/maintenance_db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
