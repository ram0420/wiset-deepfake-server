from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
print("DATABASE_URL:", DATABASE_URL)

# engine = create_engine(
#     DATABASE_URL,
#     connect_args={"sslmode": "require"}  # ✅ Supabase PostgreSQL은 SSL 필요
# )
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "sslmode": "require"
    } if DATABASE_URL.startswith("postgresql") else {
        "check_same_thread": False
    }
)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
