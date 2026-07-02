from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Data Directories
RAW_DATA_PATH = PROJECT_ROOT / "app" / "data" / "raw"
PROCESSED_DATA_PATH = PROJECT_ROOT / "app" / "data" / "processed"
VECTOR_STORE_PATH = PROJECT_ROOT / "app" / "data" / "vector_store"