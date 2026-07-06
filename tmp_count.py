from sqlalchemy import create_engine, text

def main():
    engine = create_engine("postgresql+psycopg2://bearing:Couspdata@localhost:5432/ids_db")
    with engine.connect() as conn:
        for tbl in ["cholera.cas_maladie", "cholera.cas_ll"]:
            try:
                c = conn.execute(text(f"select count(*) from {tbl}")).scalar()
                print(tbl, c)
            except Exception as e:
                print(tbl, "ERROR", e)

if __name__ == '__main__':
    main()
