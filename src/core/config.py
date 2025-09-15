import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
class Config:
    DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
    BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    
    # Models
    MODEL_VL_PLUS = "qwen-vl-plus"
    MODEL_VL_MAX = "qwen-vl-max"
    MODEL_MAX = "qwen-max"
    MODEL_PLUS = "qwen-plus"
    
    # Database
    DB_URL = "sqlite:///finexa.db"  # We'll use SQLite for now
    
    # Input/Output paths
    INPUT_DIR = "input"
    PROCESSED_DIR = "processed"
    LOGS_DIR = "logs"
    
    # Batch size
    BATCH_SIZE = 50

# Export config
config = Config()
