from pathlib import Path
import subprocess,sys
HERE=Path(__file__).resolve().parent
for s in ['01_prepare_data.py','02_generate_eda.py','03_fit_models.py','04_validate_aemo_and_subgroups.py']:
 print(f'\n=== {s} ==='); subprocess.run([sys.executable,str(HERE/s)],check=True)
print('\nComplete. See outputs/ and data/processed/.')
