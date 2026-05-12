import os

def clean_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace common emojis with text
    content = content.replace('🚀', 'STARTING:')
    content = content.replace('📊', 'DATA:')
    content = content.replace('✅', 'SUCCESS:')
    content = content.replace('❌', 'ERROR:')
    content = content.replace('⚠️', 'WARNING:')
    content = content.replace('📤', 'UPLOAD:')
    content = content.replace('📧', 'EMAIL:')
    content = content.replace('🔄', 'RETRY:')
    content = content.replace('🕒', 'WAIT:')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

project_root = r'c:\Users\G.Ganesh\Downloads\bulk email\bulk_email_sending_marketing_UI_best'
clean_file(os.path.join(project_root, 'app.py'))
clean_file(os.path.join(project_root, 'supabase_service.py'))
print("Cleanup complete.")
