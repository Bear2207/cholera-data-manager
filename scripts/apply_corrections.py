"""Apply value corrections from data/replace_values.xlsx.

Usage:
  python scripts/apply_corrections.py [--apply]

By default runs in dry-run mode and prints the UPDATE statements and affected row counts.
Set --apply to actually execute the updates.

Works by reading sheet 'valeurs' with columns:
  - Original: regex pattern
  - Renamed: replacement string
  - Variable: target column name
  - Regex_valide: flag (VRAI/TRUE/1) to apply

The script discovers which table(s) contain the target column (in the current DB)
and applies the regex replacement to each matching table.column.
"""
from pathlib import Path
import os
import re
import sys
import csv
import logging
import datetime
import pandas as pd
from sqlalchemy import create_engine, text

DB_DIR = Path(__file__).resolve().parents[1] / 'db'
REPLACE_XLSX = Path('data') / 'replace_values.xlsx'

ALLOWED_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def get_engine():
    user = os.environ.get('POSTGRES_USER', 'bearing')
    password = os.environ.get('POSTGRES_PASSWORD', 'Couspdata')
    db = os.environ.get('POSTGRES_DB', 'ids_db')
    host = os.environ.get('POSTGRES_HOST', 'localhost')
    port = os.environ.get('POSTGRES_PORT', '5432')
    url = f'postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}'
    return create_engine(url)


def load_rules(path):
    if not path.exists():
        raise FileNotFoundError(path)
    xls = pd.ExcelFile(path)
    df = pd.read_excel(path, sheet_name=xls.sheet_names[0])
    # Normalize column names
    df.columns = [c.strip() for c in df.columns]
    return df


def is_truthy(v):
    if pd.isna(v):
        return False
    s = str(v).strip().upper()
    return s in ('VRAI', 'TRUE', '1', 'OUI', 'YES')


def find_tables_for_column(conn, column):
    q = text("""
        SELECT table_schema, table_name, column_name
        FROM information_schema.columns
        WHERE column_name ILIKE :col
    """)
    rows = conn.execute(q, {'col': column}).fetchall()
    # return schema, table, actual_column_name
    return [(r.table_schema, r.table_name, r.column_name) for r in rows]


def apply_rule(conn, schema, table, column, pattern, replacement, do_apply=False):
    # Quote identifiers safely (we validated column name)
    full_table = f'"{schema}"."{table}"'
    col_ident = f'"{column}"'
    # Count before
    count_q = text(f"SELECT count(*) FROM {full_table} WHERE {col_ident} ~* :pattern")
    try:
        c = conn.execute(count_q, {'pattern': pattern}).scalar()
    except Exception as e:
        # likely invalid regular expression; report and skip
        return 0, f'ERROR_INVALID_REGEX: {e}'
    if c == 0:
        return 0, None
    update_q = text(f"UPDATE {full_table} SET {col_ident} = regexp_replace({col_ident}, :pattern, :replacement, 'gi') WHERE {col_ident} ~* :pattern")
    if do_apply:
        try:
            res = conn.execute(update_q, {'pattern': pattern, 'replacement': replacement})
            return res.rowcount, update_q.text
        except Exception as e:
            return 0, f'ERROR_UPDATE: {e}'
    else:
        return c, update_q.text


def main():
    apply_changes = '--apply' in sys.argv
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
    logger = logging.getLogger(__name__)
    print_mode = logger.info
    print_mode('Apply mode: %s', apply_changes)
    df = load_rules(REPLACE_XLSX)
    engine = get_engine()
    rules = []
    for i, row in df.iterrows():
        pattern = str(row.get('Original','')).strip()
        replacement = str(row.get('Renamed','')).strip()
        variable = str(row.get('Variable','')).strip()
        regex_flag = row.get('Regex_valide', '')
        if not pattern or not variable:
            continue
        if not is_truthy(regex_flag):
            continue
        if not ALLOWED_IDENT.match(variable):
            print('Skipping variable with unsafe name:', variable)
            continue
        rules.append((variable, pattern, replacement))

    if not rules:
        print('No valid rules found.')
        return

    summary = []
    # prepare log file
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)
    logfile = logs_dir / f'corrections_{datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.csv'
    with engine.connect() as conn:
        for variable, pattern, replacement in rules:
            try:
                tables = find_tables_for_column(conn, variable)
            except Exception as e:
                print('Error discovering tables for', variable, e)
                summary.append((variable, pattern, replacement, 'DISCOVERY_ERROR'))
                continue
            if not tables:
                summary.append((variable, pattern, replacement, 'NO_TABLE'))
                logger.warning('No table contains column %s', variable)
                continue
            for schema, table, actual_col in tables:
                # Run each rule in its own transaction so failures don't abort the whole run
                try:
                    with engine.begin() as tr:
                        affected, stmt = apply_rule(tr, schema, table, actual_col, pattern, replacement, do_apply=apply_changes)
                except Exception as e:
                    logger.exception('Error applying rule %s on %s.%s', variable, schema, table)
                    summary.append((f'{schema}.{table}', actual_col, pattern, replacement, f'ERROR: {e}'))
                    continue
                summary.append((f'{schema}.{table}', actual_col, pattern, replacement, affected))
                logger.info('Rule -> %s.%s.%s affected rows: %s', schema, table, actual_col, affected)

    # write summary CSV
    try:
        with open(logfile, 'w', newline='', encoding='utf-8') as fh:
            writer = csv.writer(fh)
            writer.writerow(['table', 'column', 'pattern', 'replacement', 'affected'])
            for s in summary:
                # some summary entries may be 'variable' style, normalize
                if len(s) == 5:
                    writer.writerow(s)
                elif len(s) == 4:
                    writer.writerow([s[0], '', s[1], s[2], s[3]])
                else:
                    writer.writerow(list(s))
        logger.info('Wrote correction log to %s', logfile)
    except Exception:
        logger.exception('Failed to write correction log')
    logger.info('Summary (first 200 rows):')
    for s in summary[:200]:
        logger.info(s)


if __name__ == '__main__':
    main()
