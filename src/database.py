import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def get_engine():
    user = os.getenv('POSTGRES_USER', 'bearing')
    password = os.getenv('POSTGRES_PASSWORD', 'Couspdata')
    db = os.getenv('POSTGRES_DB', 'ids_db')
    host = os.getenv('POSTGRES_HOST', 'localhost')
    port = os.getenv('POSTGRES_PORT', '5432')
    url = f'postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}'
    return create_engine(url, pool_pre_ping=True)