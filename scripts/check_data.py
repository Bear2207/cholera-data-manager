"""Simple data checks for cholera DB.

Usage:
  python scripts/check_data.py

Generates a quick report in logs/check_data_<timestamp>.txt
"""
from sqlalchemy import create_engine, text
from pathlib import Path
import datetime
import os


def get_engine():
    user = os.environ.get('POSTGRES_USER', 'bearing')
    password = os.environ.get('POSTGRES_PASSWORD', 'Couspdata')
    db = os.environ.get('POSTGRES_DB', 'ids_db')
    host = os.environ.get('POSTGRES_HOST', 'localhost')
    port = os.environ.get('POSTGRES_PORT', '5432')
    url = f'postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}'
    return create_engine(url)


def run_checks():
    engine = get_engine()
    report = []
    with engine.connect() as conn:
        # total counts
        for tbl in ('cholera.cas_maladie','cholera.cas_ll'):
            try:
                c = conn.execute(text(f'select count(*) from {tbl}')).scalar()
                report.append((tbl, 'count', c))
            except Exception as e:
                report.append((tbl, 'count_error', str(e)))
        # null key checks
        try:
            c = conn.execute(text("select count(*) from cholera.cas_maladie where code_zone is null or num_semaine is null or maladie is null")).scalar()
            report.append(('cholera.cas_maladie', 'null_key_count', c))
        except Exception as e:
            report.append(('cholera.cas_maladie', 'null_key_error', str(e)))
        try:
            c = conn.execute(text("select count(*) from cholera.cas_ll where n_epid is null and nom_complet is null" )).scalar()
            report.append(('cholera.cas_ll', 'null_patient_identifiers', c))
        except Exception as e:
            report.append(('cholera.cas_ll', 'null_patient_error', str(e)))
        # duplicates for unique constraint
        try:
            d = conn.execute(text("select code_zone, num_semaine, maladie, count(*) from cholera.cas_maladie group by code_zone, num_semaine, maladie having count(*)>1 limit 5")).fetchall()
            report.append(('cholera.cas_maladie', 'duplicate_samples', [tuple(r) for r in d]))
        except Exception as e:
            report.append(('cholera.cas_maladie', 'duplicate_error', str(e)))
    return report


def main():
    logs = Path('logs')
    logs.mkdir(exist_ok=True)
    fname = logs / f'check_data_{datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.txt'
    report = run_checks()
    with open(fname, 'w', encoding='utf-8') as fh:
        for item in report:
            fh.write(str(item) + '\n')
    print('Wrote report to', fname)
    for item in report:
        print(item)

if __name__ == '__main__':
    main()
