"""Centralized application configuration for SmartStock AI.

Keeps paths and application settings in one place so no component
hardcodes file locations. Contains no secrets and no business logic.
"""

from pathlib import Path

# Project root (this file lives at the repository root).
PROJECT_ROOT = Path(__file__).resolve().parent

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Name of the historical sales dataset file (Kaggle Store Item Demand).
HISTORICAL_DATASET_PATH = RAW_DATA_DIR / "train.csv"

# Operational SQLite database (generated locally; excluded from Git).
DATABASE_PATH = DATA_DIR / "smartstock.db"

# ML model artifacts
MODELS_DIR = PROJECT_ROOT / "models"
MODEL_ARTIFACTS_DIR = MODELS_DIR / "artifacts"

# Application settings
APP_TITLE = "SmartStock AI"
APP_DESCRIPTION = (
    "Smart inventory and demand forecasting for small businesses."
)
