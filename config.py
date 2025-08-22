import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL: str = "mysql+mysqlconnector://elfatih_user:123456@173.212.251.191:3306/elfatih_backend"
    
settings = Settings()
