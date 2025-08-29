import os
from dotenv import load_dotenv
load_dotenv()

# URL type : postgresql+psycopg2://user:password@host:port/dbname
DB_URL = os.getenv("DB_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/superstore")
DATA_PATH = os.getenv("DATA_PATH", "data/raw/GlobalSuperstore.txt")
ENCODING = os.getenv("ENCODING", "utf-8")
DECIMAL  = os.getenv("DECIMAL", ".")
SEP      = os.getenv("SEP", "auto")  # "auto" = détection

