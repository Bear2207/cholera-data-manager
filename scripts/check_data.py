#!/usr/bin/env python3
"""Vérification simple des comptages."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from database import get_engine
from sqlalchemy import text
import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def run_checks():
    engine = get_engine()
    report = []
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)
    logfile = logs_dir / f'check_data_{datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.txt'
    with engine.connect() as conn:
        for tbl in ('cholera.cas_maladie', 'cholera.cas_ll'):
            c = conn.execute(text(f'SELECT count(*) FROM {tbl}')).scalar()
            report.append((tbl, 'count', c))
        # Autres vérifications simples
        for tbl in ('cholera.pays', 'cholera.province', 'cholera.zone_sante', 'cholera.maladie'):
            c = conn.execute(text(f'SELECT count(*) FROM {tbl}')).scalar()
            report.append((tbl, 'count', c))
    with open(logfile, 'w', encoding='utf-8') as f:
        for item in report:
            f.write(str(item) + '\n')
    logger.info("Rapport écrit dans %s", logfile)
    for item in report:
        logger.info(item)

if __name__ == '__main__':
    run_checks()