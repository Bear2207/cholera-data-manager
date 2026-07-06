import pandas as pd
from pathlib import Path

for filename in ['db/IDS_2026.xlsx', 'db/rdc_compilation_LL_Cholera_SE01_SE52_04_01_2026_03_33_36.xlsx']:
    f = Path(filename)
    print('FILE', f)
    print('exists', f.exists())
    if not f.exists():
        continue
    xl = pd.ExcelFile(f, engine='openpyxl')
    print('sheets', xl.sheet_names)
    for sheet in xl.sheet_names[:3]:
        df = pd.read_excel(f, sheet_name=sheet, engine='openpyxl', nrows=5)
        print(' sheet', sheet)
        print(' cols', df.columns.tolist())
        print(' sample rows', df.head(2).to_dict(orient='records'))
        print()
