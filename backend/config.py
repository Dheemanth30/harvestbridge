import os

SECRET_KEY = os.environ.get("SECRET_KEY", "harvestbridge-secret-key-change-in-production-2024")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
UPLOAD_DIR = "static/uploads"
