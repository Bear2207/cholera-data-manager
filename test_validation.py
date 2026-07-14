import sys
import glob
from pathlib import Path

sys.path.insert(0, 'src')
from loaders.ids_loader import load_ids_excel
from loaders.ll_loader import load_ll_excel

ids_path = Path('data/ids/IDS_2025.xlsx')
ll_files = glob.glob('data/ll/rdc_compilation*_LL_Cholera_*.xlsx')
if not ll_files:
    raise FileNotFoundError('No LL file found')
ll_path = Path(ll_files[0])

print('Loading IDS from:', ids_path)
df_ids = load_ids_excel(ids_path)
print('IDS shape:', df_ids.shape)
print('IDS columns:', list(df_ids.columns))
print('IDS debut_semaine has nulls:', df_ids['debut_semaine'].isnull().any() if 'debut_semaine' in df_ids.columns else 'debut_semaine column missing')

print('\nLoading LL from:', ll_path)
df_ll = load_ll_excel(ll_path)
print('LL shape:', df_ll.shape)
print('LL columns:', list(df_ll.columns))

print('\nLL boolean column dtypes and unique values:')
# Check true boolean columns, or columns containing only True/False/NaN values
for col in df_ll.columns:
    unique_vals = set(df_ll[col].dropna().unique())
    if df_ll[col].dtype == 'bool':
        print(f'{col}: dtype={df_ll[col].dtype}, unique={df_ll[col].unique().tolist()}')
    elif unique_vals.issubset({True, False}) and len(unique_vals) > 0:
        print(f'{col}: dtype={df_ll[col].dtype} (boolean values), unique={df_ll[col].unique().tolist()}')
