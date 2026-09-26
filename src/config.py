from dotenv import load_dotenv
import os


load_dotenv('../.env')

class Config:
    DATABASE_URL = os.getenv("DATABASE_URL", "")
    APP_NAME = os.getenv("APP_NAME", "")

    if not APP_NAME:
        raise RuntimeError("No APP_NAME in environment variables!")

    if not DATABASE_URL:
        raise RuntimeError("No DATABASE_URL in environment variables!")
