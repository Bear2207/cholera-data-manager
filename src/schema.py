from pathlib import Path
from sqlalchemy import text

DB_DIR = Path(__file__).resolve().parents[1] / 'db'

def ensure_schema(engine):
    init_file = DB_DIR / 'init.sql'
    if not init_file.exists():
        raise FileNotFoundError(f"Fichier de schéma introuvable : {init_file}")
    sql = init_file.read_text(encoding='utf-8')
    with engine.begin() as conn:
        conn.exec_driver_sql(sql)