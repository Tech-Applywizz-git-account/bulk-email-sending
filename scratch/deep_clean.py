import os
import re

def strip_non_ascii(text):
    # This regex matches any character that is NOT in the ASCII range (0-127)
    return re.sub(r'[^\x00-\x7f]', '', text)

def clean_file(filepath):
    print(f"Cleaning {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    cleaned_content = strip_non_ascii(content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(cleaned_content)

project_root = r'c:\Users\G.Ganesh\Downloads\bulk email\bulk_email_sending_marketing_UI_best'
clean_file(os.path.join(project_root, 'app.py'))
clean_file(os.path.join(project_root, 'supabase_service.py'))
print("Deep cleanup complete.")
