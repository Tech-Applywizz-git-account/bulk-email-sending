import os
import datetime

# Root is one level up from scratch/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')

print(f"Checking UPLOAD_FOLDER: {UPLOAD_FOLDER}")
if os.path.exists(UPLOAD_FOLDER):
    print("Folder exists.")
    files = os.listdir(UPLOAD_FOLDER)
    print(f"Files found: {files}")
    for fname in files:
        if fname.endswith(('.xlsx', '.xls', '.csv')):
            print(f"MATCH: {fname}")
else:
    print("Folder does NOT exist.")
