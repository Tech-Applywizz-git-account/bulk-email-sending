from flask import Flask, request, render_template, send_from_directory, redirect, url_for, flash
import pandas as pd
from dotenv import load_dotenv
import os
import requests
import msal
import datetime
import uuid
import sys

load_dotenv()

import json
import supabase_service as sb

# Environment Variables Logging
print("="*60)
print("STARTING: FLASK APPLICATION INITIALIZATION")
print("="*60)
print(f"Python version: {sys.version}")
print(f"Environment check:")
print(f"  SECRET_KEY loaded: {os.getenv('SECRET_KEY') is not None}")
print(f"  TENANT_ID loaded: {os.getenv('TENANT_ID') is not None}")
print(f"  CLIENT_ID loaded: {os.getenv('CLIENT_ID') is not None}")
print(f"  CLIENT_SECRET loaded: {os.getenv('CLIENT_SECRET') is not None}")
print(f"  SENDER_EMAIL: {os.getenv('SENDER_EMAIL')}")
print(f"  SUPABASE_URL loaded: {os.getenv('SUPABASE_URL') is not None}")
print(f"  SUPABASE_SERVICE_KEY loaded: {os.getenv('SUPABASE_SERVICE_KEY') is not None}")
print(f"  SUPABASE_BUCKET_NAME: {os.getenv('SUPABASE_BUCKET_NAME', 'email-attachments')}")
print("="*60)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "super_secret_key_for_dev") # Needed for flash messages

# Determine storage path (use /tmp for Vercel/Serverless)
IS_VERCEL = os.environ.get('VERCEL') == '1'
BASE_DIR = '/tmp' if IS_VERCEL else os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
LOGS_FOLDER = os.path.join(BASE_DIR, 'logs')
UPLOAD_JSON_FOLDER = os.path.join(BASE_DIR, 'json_uploads')
LOGS_JSON_FOLDER = os.path.join(BASE_DIR, 'json_logs')
DEBUG_LOG_PATH = os.path.join(BASE_DIR, 'upload_debug.log')

# Ensure directories exist
for folder in [UPLOAD_FOLDER, LOGS_FOLDER, UPLOAD_JSON_FOLDER, LOGS_JSON_FOLDER]:
    os.makedirs(folder, exist_ok=True)

print(f"Using Storage Path: {BASE_DIR}")

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['LOGS_FOLDER'] = LOGS_FOLDER
app.config['UPLOAD_JSON_FOLDER'] = UPLOAD_JSON_FOLDER
app.config['LOGS_JSON_FOLDER'] = LOGS_JSON_FOLDER




@app.route('/')
def index():
    """Display all uploaded files - merges Supabase and local storage"""
    files_dict = {} # Use dict to avoid duplicates by filename

    # 1. Load local files first (most reliable)
    try:
        if os.path.exists(app.config['UPLOAD_FOLDER']):
            for fname in os.listdir(app.config['UPLOAD_FOLDER']):
                if fname.endswith(('.xlsx', '.xls', '.csv')):
                    fpath = os.path.join(app.config['UPLOAD_FOLDER'], fname)
                    mtime = os.path.getmtime(fpath)
                    fsize = os.path.getsize(fpath)
                    dt = datetime.datetime.fromtimestamp(mtime)
                    date_str = dt.strftime('%Y-%m-%d %I:%M %p')
                    files_dict[fname] = {
                        'name': fname,
                        'date': date_str,
                        'timestamp': mtime,
                        'id': None,
                        'size': fsize,
                        'source': 'local'
                    }
    except Exception as e:
        print(f"ERROR: Could not load local files: {e}")

    # 2. Load Supabase files and merge (Supabase files take precedence for IDs)
    if sb.is_supabase_enabled():
        try:
            db_files = sb.get_all_uploaded_files()
            ist_offset = datetime.timedelta(hours=5, minutes=30)
            for db_file in db_files:
                fname = db_file.get('filename', '')
                if not fname: continue
                
                upload_date = db_file.get('upload_date')
                if upload_date:
                    try:
                        if isinstance(upload_date, str):
                            dt_object = datetime.datetime.fromisoformat(upload_date.replace('Z', '+00:00'))
                        else:
                            dt_object = upload_date
                        ist_time = dt_object + ist_offset
                        date_str = ist_time.strftime('%Y-%m-%d %I:%M %p')
                        timestamp = dt_object.timestamp()
                    except:
                        date_str = 'Unknown'
                        timestamp = 0
                else:
                    date_str = 'Unknown'
                    timestamp = 0
                
                # Merge or add
                files_dict[fname] = {
                    'name': fname,
                    'date': date_str,
                    'timestamp': timestamp,
                    'id': db_file.get('id'),
                    'size': db_file.get('file_size', 0),
                    'source': 'supabase'
                }
            print(f"INFO: Merged {len(db_files)} files from Supabase")
        except Exception as e:
            print(f"WARNING: Supabase unavailable during merge: {e}")

    # Convert to list and sort by timestamp
    files = sorted(files_dict.values(), key=lambda x: x['timestamp'], reverse=True)
    return render_template('index.html', files=files)


@app.route('/debug')
def debug_status():
    """Display system diagnostics and configuration status"""
    import platform
    
    # Check environment variables
    env_vars = {
        'SECRET_KEY': os.getenv('SECRET_KEY') is not None,
        'SECRET_KEY_length': len(os.getenv('SECRET_KEY', '')) if os.getenv('SECRET_KEY') else 0,
        'TENANT_ID': os.getenv('TENANT_ID'),
        'CLIENT_ID': os.getenv('CLIENT_ID'),
        'CLIENT_SECRET': os.getenv('CLIENT_SECRET') is not None,
        'SENDER_EMAIL': os.getenv('SENDER_EMAIL'),
        'SUPABASE_URL': os.getenv('SUPABASE_URL'),
        'SUPABASE_SERVICE_KEY': os.getenv('SUPABASE_SERVICE_KEY') is not None,
        'SUPABASE_SERVICE_KEY_length': len(os.getenv('SUPABASE_SERVICE_KEY', '')) if os.getenv('SUPABASE_SERVICE_KEY') else 0,
        'SUPABASE_SERVICE_KEY_start': os.getenv('SUPABASE_SERVICE_KEY', '')[:20] if os.getenv('SUPABASE_SERVICE_KEY') else 'N/A',
        'SUPABASE_BUCKET_NAME': os.getenv('SUPABASE_BUCKET_NAME', 'email-attachments')
    }
    
    # Check Supabase connection
    supabase_status = {
        'enabled': sb.is_supabase_enabled(),
        'error': None,
        'can_read': False,
        'can_write': False,
        'file_count': 0,
        'test_details': []
    }
    
    if not sb.is_supabase_enabled():
        if not os.getenv('SUPABASE_URL'):
            supabase_status['error'] = 'SUPABASE_URL environment variable is not set'
        elif not os.getenv('SUPABASE_SERVICE_KEY'):
            supabase_status['error'] = 'SUPABASE_SERVICE_KEY environment variable is not set (check the exact variable name)'
        else:
            supabase_status['error'] = 'Failed to initialize Supabase client with provided credentials'
    else:
        # Test READ access
        try:
            files = sb.get_all_uploaded_files()
            supabase_status['can_read'] = True
            supabase_status['file_count'] = len(files)
            supabase_status['test_details'].append(f"SUCCESS: READ access works - Found {len(files)} files")
        except Exception as e:
            supabase_status['can_read'] = False
            supabase_status['test_details'].append(f"ERROR: READ access failed: {str(e)}")
            supabase_status['error'] = f"READ permission denied. This is likely a Row Level Security (RLS) policy issue. Error: {str(e)}"
    
    # System information
    system_info = {
        'python_version': sys.version,
        'platform': platform.platform(),
        'current_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')
    }
    
    # Count issues
    issues_count = 0
    if not env_vars['SECRET_KEY']:
        issues_count += 1
    if not env_vars['TENANT_ID']:
        issues_count += 1
    if not env_vars['CLIENT_ID']:
        issues_count += 1
    if not env_vars['CLIENT_SECRET']:
        issues_count += 1
    if not env_vars['SENDER_EMAIL']:
        issues_count += 1
    if not env_vars['SUPABASE_URL']:
        issues_count += 1
    if not env_vars['SUPABASE_SERVICE_KEY']:
        issues_count += 1
    if not supabase_status['enabled']:
        issues_count += 1
    if not supabase_status['can_read']:
        issues_count += 1
    
    overall_healthy = issues_count == 0
    
    return render_template('debug.html', 
                         env_vars=env_vars,
                         supabase_status=supabase_status,
                         system_info=system_info,
                         issues_count=issues_count,
                         overall_healthy=overall_healthy)



@app.route('/logs')
def list_logs():
    """Display all email sending batches - merges Supabase and local log files"""
    batches_dict = {}

    # 1. Load local log files
    try:
        if os.path.exists(app.config['LOGS_FOLDER']):
            for fname in os.listdir(app.config['LOGS_FOLDER']):
                if fname.endswith(('.xlsx', '.xls')):
                    fpath = os.path.join(app.config['LOGS_FOLDER'], fname)
                    mtime = os.path.getmtime(fpath)
                    dt = datetime.datetime.fromtimestamp(mtime)
                    display_date = dt.strftime('%Y-%m-%d %I:%M %p')
                    batches_dict[fname] = {
                        'batch_id': fname,
                        'filename': fname,
                        'date': display_date,
                        'count': '?',
                        'source': 'local',
                        'timestamp': mtime
                    }
    except Exception as e:
        print(f"ERROR: Could not load local logs: {e}")

    # 2. Load Supabase logs and merge
    if sb.is_supabase_enabled():
        try:
            batches_data = sb.get_all_email_batches()
            for batch in batches_data:
                batch_id = batch.get('batch_id')
                if not batch_id: continue
                
                sent_at_str = batch.get('sent_at', '')
                if sent_at_str:
                    try:
                        if isinstance(sent_at_str, str):
                            dt_object = datetime.datetime.fromisoformat(sent_at_str.replace('Z', '+00:00'))
                        else:
                            dt_object = sent_at_str
                        ist_offset = datetime.timedelta(hours=5, minutes=30)
                        ist_time = dt_object + ist_offset
                        display_date = ist_time.strftime('%Y-%m-%d %I:%M %p')
                        timestamp = dt_object.timestamp()
                    except:
                        display_date = sent_at_str
                        timestamp = 0
                else:
                    display_date = 'Unknown'
                    timestamp = 0
                
                source_file_id = batch.get('source_file_id')
                filename = 'Unknown'
                if source_file_id:
                    try:
                        file_record = sb.get_file_by_id(source_file_id)
                        if file_record:
                            filename = file_record.get('filename', 'Unknown')
                    except:
                        pass
                
                # If we have a local file with the same name, the Supabase record might be better
                # but batch_id is unique in Supabase.
                batches_dict[batch_id] = {
                    'batch_id': batch_id,
                    'filename': filename,
                    'date': display_date,
                    'count': batch.get('count', 0),
                    'source': 'supabase',
                    'timestamp': timestamp
                }
            print(f"INFO: Merged {len(batches_data)} log batches from Supabase")
        except Exception as e:
            print(f"WARNING: Supabase unavailable for log merge: {e}")

    batches = sorted(batches_dict.values(), key=lambda x: x['timestamp'], reverse=True)
    return render_template('logs.html', files=batches)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(request.url)
        
    if file and file.filename.endswith(('.xlsx', '.xls', '.csv')):
        try:
            # Save to local filesystem first
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            file_size = os.path.getsize(filepath)
            with open(DEBUG_LOG_PATH, "a") as logf:
                logf.write(f"\n--- UPLOAD START: {file.filename} ---\n")
                logf.write(f"DEBUG: File saved locally to {filepath} (Size: {file_size} bytes)\n")
            
            # Parse Excel data
            data = parse_excel(filepath)
            with open(DEBUG_LOG_PATH, "a") as logf:
                logf.write(f"DEBUG: Excel parsed, rows found: {len(data)}\n")
            
            # Convert to JSON and store locally
            try:
                json_filename = os.path.splitext(file.filename)[0] + '.json'
                json_filepath = os.path.join(app.config['UPLOAD_JSON_FOLDER'], json_filename)
                with open(json_filepath, 'w') as f:
                    json.dump(data, f, indent=4)
                with open(DEBUG_LOG_PATH, "a") as logf:
                    logf.write(f"DEBUG: JSON saved to {json_filepath}\n")
            except Exception as json_e:
                with open(DEBUG_LOG_PATH, "a") as logf:
                    logf.write(f"DEBUG: Error saving JSON: {json_e}\n")

            # Upload to Supabase Storage and Database
            with open(DEBUG_LOG_PATH, "a") as logf:
                logf.write(f"DEBUG: Starting Supabase sync...\n")
                logf.write(f"DEBUG: Supabase enabled check: {sb.is_supabase_enabled()}\n")
            
            if sb.is_supabase_enabled():
                try:
                    with open(DEBUG_LOG_PATH, "a") as logf:
                        logf.write(f"DEBUG: Attempting storage upload for {file.filename}...\n")
                    storage_path = sb.upload_file_to_storage(filepath, file.filename)
                    with open(DEBUG_LOG_PATH, "a") as logf:
                        logf.write(f"DEBUG: Storage path result: {storage_path}\n")
                    
                    if not storage_path:
                        with open(DEBUG_LOG_PATH, "a") as logf:
                            logf.write("DEBUG: WARNING: Storage upload failed, but proceeding with database record insertion using local path.\n")
                        storage_path = f"local://{file.filename}"
                    
                    with open(DEBUG_LOG_PATH, "a") as logf:
                        logf.write(f"DEBUG: Attempting database record insertion with path: {storage_path}...\n")
                    
                    file_id = sb.insert_uploaded_file(
                        filename=file.filename,
                        original_filename=file.filename,
                        storage_path=storage_path,
                        file_size=file_size,
                        metadata={'emails': data}
                    )
                    with open(DEBUG_LOG_PATH, "a") as logf:
                        logf.write(f"DEBUG: Database file_id result: {file_id}\n")
                    
                    if file_id:
                        sb.insert_upload_log(
                            file_id=file_id,
                            action="upload",
                            status="success",
                            details=f"Uploaded {file.filename}",
                            ip_address=request.remote_addr or ""
                        )
                        with open(DEBUG_LOG_PATH, "a") as logf:
                            logf.write(f"DEBUG: SUCCESS: Sync complete for {file.filename}\n")
                    else:
                        with open(DEBUG_LOG_PATH, "a") as logf:
                            logf.write("DEBUG: ERROR: Database insertion failed (returned None)\n")
                except Exception as sb_e:
                    with open(DEBUG_LOG_PATH, "a") as logf:
                        logf.write(f"DEBUG: EXCEPTION during Supabase sync: {sb_e}\n")
            else:
                with open(DEBUG_LOG_PATH, "a") as logf:
                    logf.write("DEBUG: Supabase not enabled/reachable, skipping sync.\n")

            flash(f'File "{file.filename}" uploaded successfully!', 'success')
        except Exception as e:
            with open(DEBUG_LOG_PATH, "a") as logf:
                logf.write(f"DEBUG: CRITICAL ERROR in upload_file: {e}\n")
            flash(f'Error saving file: {str(e)}', 'error')
        return redirect(url_for('index'))
    
    flash('Invalid file format. Please upload .xlsx, .xls or .csv', 'error')
    return redirect(url_for('index'))

@app.route('/files/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/logs/download/<filename>')
def download_log(filename):
    return send_from_directory(app.config['LOGS_FOLDER'], filename)

@app.route('/delete/upload/<filename>', methods=['POST'])
def delete_upload(filename):
    # Delete from Supabase first
    if sb.is_supabase_enabled():
        try:
            db_file = sb.get_file_by_filename(filename)
            if db_file:
                file_id = db_file.get('id')
                storage_path = db_file.get('file_path')
                
                # Log deletion
                sb.insert_upload_log(
                    file_id=file_id,
                    action="delete",
                    status="success",
                    details=f"Deleted {filename}",
                    ip_address=request.remote_addr or ""
                )
                
                # Delete from storage
                sb.delete_file_from_storage(storage_path)
                
                # Delete from database
                sb.delete_file_record(file_id)
                
                print(f"SUCCESS: File deleted from Supabase: {filename}")
        except Exception as e:
            print(f"WARNING: Error deleting from Supabase: {e}")
    
    # Delete from local filesystem
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            
            # Try removing corresponding JSON
            json_filename = os.path.splitext(filename)[0] + '.json'
            json_filepath = os.path.join(app.config['UPLOAD_JSON_FOLDER'], json_filename)
            if os.path.exists(json_filepath):
                os.remove(json_filepath)

            flash(f'File "{filename}" deleted successfully.', 'success')
        except Exception as e:
            flash(f"Error deleting file: {e}", 'error')
    else:
        flash('File not found.', 'error')
    return redirect(url_for('index'))

@app.route('/delete/log/<filename>', methods=['POST'])
def delete_log(filename):
    filepath = os.path.join(app.config['LOGS_FOLDER'], filename)
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            
            # Try deleting corresponding JSON log if naming convention matches
            # The log naming is log_TIMESTAMP_filename.xlsx
            # We will save JSON as log_TIMESTAMP_filename.json
            json_filename = os.path.splitext(filename)[0] + '.json'
            json_filepath = os.path.join(app.config['LOGS_JSON_FOLDER'], json_filename)
            if os.path.exists(json_filepath):
                os.remove(json_filepath)

            flash(f'Log file "{filename}" deleted successfully.', 'success')
        except Exception as e:
             flash(f"Error deleting file: {e}", 'error')
    else:
        flash('Log file not found.', 'error')
    return redirect(url_for('list_logs'))

@app.route('/view/<filename>')
def view_file(filename):
    """View uploaded file - Uses Supabase Signed URL if possible"""
    # 1. Try to get a signed URL from Supabase first (best for Vercel)
    if sb.is_supabase_enabled():
        try:
            db_file = sb.get_file_by_filename(filename)
            if db_file:
                storage_path = db_file.get('file_path')
                if storage_path and not storage_path.startswith('local://'):
                    # Get a temporary signed URL (valid for 1 hour)
                    signed_url = sb.get_file_download_url(storage_path)
                    if signed_url:
                        # If we have a signed URL, we can redirect or parse from URL
                        # For simplicity, we'll still try to parse it locally if possible,
                        # but we'll download it to /tmp first
                        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        if not os.path.exists(filepath):
                            sb.download_file_from_storage(storage_path, filepath)
                        
                        if os.path.exists(filepath):
                            data = parse_excel(filepath)
                            return render_template('view.html', filename=filename, emails=data)
            
            print(f"DEBUG: Falling back to local check for {filename}")
        except Exception as e:
            print(f"ERROR: Supabase view error: {e}")

    # 2. Fallback to local filesystem
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        flash('File could not be retrieved from cloud or local storage.', 'error')
        return redirect(url_for('index'))
        
    data = parse_excel(filepath)
    return render_template('view.html', filename=filename, emails=data)

@app.route('/logs/view/<path:batch_id>')
def view_log(batch_id):
    """View email logs for a specific batch - supports both Supabase and local logs"""
    logs = []
    filename = 'Unknown'
    
    # 1. Try Supabase first if enabled
    if sb.is_supabase_enabled():
        try:
            logs_data = sb.get_email_logs_by_batch(batch_id)
            if logs_data:
                first_log = logs_data[0]
                source_file_id = first_log.get('source_file_id')
                if source_file_id:
                    file_record = sb.get_file_by_id(source_file_id)
                    if file_record:
                        filename = file_record.get('filename', 'Unknown')
                
                for log in logs_data:
                    sent_at_str = log.get('sent_at', '')
                    if sent_at_str:
                        try:
                            if isinstance(sent_at_str, str):
                                dt_object = datetime.datetime.fromisoformat(sent_at_str.replace('Z', '+00:00'))
                            else:
                                dt_object = sent_at_str
                            ist_offset = datetime.timedelta(hours=5, minutes=30)
                            ist_time = dt_object + ist_offset
                            timestamp = ist_time.strftime('%Y-%m-%d %I:%M:%S %p')
                        except:
                            timestamp = sent_at_str
                    else:
                        timestamp = 'Unknown'
                    
                    logs.append({
                        'Timestamp': timestamp,
                        'Recipient Name': log.get('recipient_name', ''),
                        'Recipient Email': log.get('recipient_email', ''),
                        'Subject': log.get('subject', ''),
                        'Status': log.get('status', ''),
                        'Details': log.get('details', '')
                    })
        except Exception as e:
            print(f"WARNING: Error loading logs from Supabase: {e}")

    # 2. If no logs found in Supabase (or Supabase disabled), check local files
    if not logs:
        # batch_id might be a filename like 'log_TIMESTAMP_original.xlsx'
        local_path = os.path.join(app.config['LOGS_FOLDER'], batch_id)
        if os.path.exists(local_path):
            try:
                df = pd.read_excel(local_path)
                df = df.fillna('')
                # Standardize column names if needed
                filename = batch_id
                for _, row in df.iterrows():
                    logs.append({
                        'Timestamp': row.get('Timestamp', 'N/A'),
                        'Recipient Name': row.get('Recipient Name', row.get('Name', '')),
                        'Recipient Email': row.get('Recipient Email', row.get('Email', '')),
                        'Subject': row.get('Subject', ''),
                        'Status': row.get('Status', ''),
                        'Details': row.get('Details', '')
                    })
                print(f"INFO: Loaded {len(logs)} logs from local file: {batch_id}")
            except Exception as e:
                print(f"ERROR: Error reading local log file: {e}")

    if not logs:
        flash('No log data found for this batch', 'warning')
        return redirect(url_for('list_logs'))
    
    return render_template('view_log.html', filename=filename, logs=logs, batch_id=batch_id)
    
    return render_template('view_log.html', filename=filename, logs=logs, batch_id=batch_id)

def parse_excel(filepath):
    try:
        df = pd.read_excel(filepath)
        df = df.fillna('')
        
        # Normalize columns: strip whitespace and convert to title case for matching
        df.columns = [str(col).strip().title() for col in df.columns]
        
        # Map common variations if needed, or rely on Title Case
        # e.g. 'email' -> 'Email', 'Email Body' -> 'Email Body'
        
        data = []
        for _, row in df.iterrows():
            data.append({
                'name': row.get('Name', ''),
                'email': row.get('Email', ''),
                'subject': row.get('Subject', 'No Subject'),
                'body': row.get('Email Body', '') or row.get('Body', '') # Fallback to 'Body'
            })
        return data
    except Exception as e:

        print(f"Error parsing Excel: {e}")
        return []

@app.route('/send-emails/<filename>', methods=['POST'])
def send_emails(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    # Try to get file from Supabase if not in local cache
    if not os.path.exists(filepath) and sb.is_supabase_enabled():
        try:
            db_file = sb.get_file_by_filename(filename)
            if db_file:
                storage_path = db_file.get('file_path')
                if storage_path and not storage_path.startswith('local://'):
                    if sb.download_file_from_storage(storage_path, filepath):
                        print(f" Downloaded file from Supabase for sending: {filename}")
        except Exception as e:
            print(f"WARNING: Could not download from Supabase: {e}")
    
    if not os.path.exists(filepath):
        flash(f"Error: File '{filename}' could not be loaded for sending. Please re-upload.", 'error')
        return redirect(url_for('index'))
        
    email_data = parse_excel(filepath)
    
    # Get file_id from Supabase if available
    file_id = None
    if sb.is_supabase_enabled():
        try:
            db_file = sb.get_file_by_filename(filename)
            if db_file:
                file_id = db_file.get('id')
        except Exception as e:
            print(f"WARNING: Could not get file_id: {e}")
    
    tenant_id = os.getenv("TENANT_ID")
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    sender_email = os.getenv("SENDER_EMAIL", "support@applywizz.com")

    # Detailed logging for Azure credentials
    print("\n" + "="*60)
    print("EMAIL: EMAIL SENDING - CREDENTIAL CHECK")
    print("="*60)
    print(f"TENANT_ID: {tenant_id[:20] + '...' if tenant_id else 'MISSING'}")
    print(f"CLIENT_ID: {client_id[:20] + '...' if client_id else 'MISSING'}")
    print(f"CLIENT_SECRET: {'*' * 20 if client_secret else 'MISSING'}")
    print(f"SENDER_EMAIL: {sender_email}")
    print(f"File ID: {file_id}")
    print("="*60 + "\n")

    if not all([tenant_id, client_id, client_secret]):
        print("ERROR: ERROR: Missing Azure credentials!")
        flash("Error: Missing Azure credentials (TENANT_ID, CLIENT_ID, CLIENT_SECRET) in .env file.", 'error')
        return redirect(url_for('view_file', filename=filename))

    # 1. Get Access Token via MSAL
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    app_msal = msal.ConfidentialClientApplication(
        client_id,
        authority=authority,
        client_credential=client_secret
    )
    
    result = app_msal.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])

    print(f" Azure Token Acquisition Result:")
    print(f"   Success: {'access_token' in result}")
    if "access_token" not in result:
        print(f"   ERROR: Error: {result.get('error')}")
        print(f"   Description: {result.get('error_description')}")
        flash(f"Error acquiring token: {result.get('error_description')}", 'error')
        return redirect(url_for('view_file', filename=filename))

    access_token = result['access_token']
    print(f"   SUCCESS: Token acquired successfully (length: {len(access_token)} chars)")
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    # 2. Send Emails
    endpoint = f"https://graph.microsoft.com/v1.0/users/{sender_email}/sendMail"
    
    success_count = 0
    errors = []
    
    # Generate batch_id for this sending session
    batch_id = str(uuid.uuid4())
    
    # Store log data
    log_entries = []

    print(f"\n Starting email batch send - {len(email_data)} emails")
    email_send_count = 0
    
    for email in email_data:
        email_send_count += 1
        status = "Skipped"
        details = "Missing email address"
        
        if email_send_count <= 3 or email_send_count == len(email_data):
            print(f"   [{email_send_count}/{len(email_data)}] Processing: {email.get('email', 'N/A')}")
        elif email_send_count == 4:
            print(f"   ... processing emails 4 to {len(email_data)-1} ...")
        
        if email['email']:
            email_msg = {
                "message": {
                    "subject": email['subject'],
                    "body": {
                        "contentType": "Text",
                        "content": email['body']
                    },
                    "toRecipients": [
                        {
                            "emailAddress": {
                                "address": email['email']
                            }
                        }
                    ]
                },
                "saveToSentItems": "true"
            }

            try:
                response = requests.post(endpoint, headers=headers, json=email_msg)
                if response.status_code == 202:
                    success_count += 1
                    status = "Success"
                    details = "Sent via MS Graph"
                else:
                    status = "Failed"
                    try:
                        error_detail = response.json()
                    except:
                        error_detail = response.text
                    details = f"API Error: {error_detail}"
                    errors.append(f"Failed to send to {email['email']}: {details}")
            except Exception as e:
                status = "Error"
                details = str(e)
                errors.append(f"Exception sending to {email['email']}: {details}")

        ist_offset = datetime.timedelta(hours=5, minutes=30)
        ist_now = datetime.datetime.utcnow() + ist_offset
        
        log_entry = {
            "Timestamp": ist_now.strftime("%Y-%m-%d %I:%M:%S %p"),
            "Recipient Name": email['name'],
            "Recipient Email": email['email'],
            "Subject": email['subject'],
            "Status": status,
            "Details": str(details)
        }
        log_entries.append(log_entry)
        
        # Log to Supabase in real-time
        if sb.is_supabase_enabled():
            try:
                log_id = sb.insert_email_log(
                    batch_id=batch_id,
                    source_file_id=file_id,
                    recipient_name=email['name'],
                    recipient_email=email['email'],
                    subject=email['subject'],
                    email_body=email['body'],
                    status=status,
                    details=str(details)
                )
                if log_id and email_send_count <= 3:
                    print(f"      SUCCESS: Logged to Supabase (log_id: {log_id[:8]}...)")
            except Exception as sb_e:
                print(f"      WARNING: Failed to log to Supabase: {sb_e}")
        else:
            if email_send_count <= 3:
                print(f"      WARNING: Supabase not enabled, skipping database log")

    # Save Log File (for backward compatibility)
    if log_entries:
        try:
            ist_offset = datetime.timedelta(hours=5, minutes=30)
            ist_now = datetime.datetime.utcnow() + ist_offset
            timestamp_str = ist_now.strftime("%Y%m%d_%H%M%S")
            log_filename = f"log_{timestamp_str}_{filename}"
            log_filepath = os.path.join(app.config['LOGS_FOLDER'], log_filename)
            
            log_df = pd.DataFrame(log_entries)
            log_df.to_excel(log_filepath, index=False)
            
            # SAVE JSON LOG
            json_log_filename = f"log_{timestamp_str}_{os.path.splitext(filename)[0]}.json"
            json_log_filepath = os.path.join(app.config['LOGS_JSON_FOLDER'], json_log_filename)
            with open(json_log_filepath, 'w') as f:
                json.dump(log_entries, f, indent=4)
            
            # Upload log file to Supabase Storage
            if sb.is_supabase_enabled():
                try:
                    sb.upload_file_to_storage(log_filepath, log_filename)
                    print(f"SUCCESS: Log file uploaded to Supabase: {log_filename}")
                except Exception as sb_e:
                    print(f"WARNING: Failed to upload log to Supabase: {sb_e}")
                
            print(f"Log saved to {log_filepath} and {json_log_filepath}")
        except Exception as e:
            errors.append(f"Failed to save log file: {e}")

    result_message = f'Successfully sent {success_count} emails!'
    if errors:
        result_message = f'Sent {success_count} emails. Errors occurred.'
        flash(result_message + " Check logs for details.", 'warning')
    else:
        flash(result_message, 'success')
        
    return redirect(url_for('list_logs'))



def save_to_excel(filepath, data):
    try:
        df = pd.DataFrame(data)
        # Ensure columns are in correct order if possible, or just default
        df.to_excel(filepath, index=False)
        return True
    except Exception as e:
        print(f"Error saving Excel: {e}")
        return False

@app.route('/files/<filename>/add', methods=['POST'])
def add_row(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        flash("File not found", "error")
        return redirect(url_for('view_file', filename=filename))

    new_data = {
        'Name': request.form.get('name'),
        'Email': request.form.get('email'),
        'Subject': request.form.get('subject'),
        'Email Body': request.form.get('body')
    }

    try:
        df = pd.read_excel(filepath)
        df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
        df.to_excel(filepath, index=False)
        flash("Recipient added successfully!", "success")
    except Exception as e:
        flash(f"Error adding row: {e}", "error")

    return redirect(url_for('view_file', filename=filename))

@app.route('/files/<filename>/edit', methods=['POST'])
def edit_row(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        flash("File not found", "error")
        return redirect(url_for('view_file', filename=filename))

    try:
        row_id = int(request.form.get('row_id'))
        df = pd.read_excel(filepath)
        
        if 0 <= row_id < len(df):
            df.at[row_id, 'Name'] = request.form.get('name')
            df.at[row_id, 'Email'] = request.form.get('email')
            df.at[row_id, 'Subject'] = request.form.get('subject')
            df.at[row_id, 'Email Body'] = request.form.get('body')
            
            df.to_excel(filepath, index=False)
            flash("Recipient updated successfully!", "success")
        else:
            flash("Invalid row ID", "error")
            
    except Exception as e:
        flash(f"Error updating row: {e}", "error")

    return redirect(url_for('view_file', filename=filename))

@app.route('/files/<filename>/delete_rows', methods=['POST'])
def delete_rows(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return "File not found", 404

    try:
        indices = request.json.get('indices', [])
        if not indices:
            return "No rows selected", 400

        df = pd.read_excel(filepath)
        df = df.drop(index=indices)
        df.to_excel(filepath, index=False)
        
        return "Rows deleted successfully", 200
    except Exception as e:
        return f"Error deleting rows: {e}", 500

@app.route('/logs/download_failed/<batch_id>')
def download_failed_log(batch_id):
    """Download failed email records for a specific batch"""
    if not sb.is_supabase_enabled():
        flash("Supabase not configured", "error")
        return redirect(url_for('list_logs'))

    try:
        # Get all logs for this batch from database
        logs_data = sb.get_email_logs_by_batch(batch_id)
        
        if not logs_data:
            flash("No logs found for this batch.", "warning")
            return redirect(url_for('list_logs'))
        
        # Filter only failed/error/skipped records
        failed_logs = [log for log in logs_data if log.get('status') not in ['Success']]
        
        if not failed_logs:
            flash("No failed entries found in this batch.", "info")
            return redirect(url_for('view_log', batch_id=batch_id))
        
        # Format for Excel export
        export_data = []
        for log in failed_logs:
            sent_at_str = log.get('sent_at', '')
            
            # Parse timestamp
            if sent_at_str:
                try:
                    if isinstance(sent_at_str, str):
                        dt_object = datetime.datetime.fromisoformat(sent_at_str.replace('Z', '+00:00'))
                    else:
                        dt_object = sent_at_str
                    
                    # Convert to IST
                    ist_offset = datetime.timedelta(hours=5, minutes=30)
                    ist_time = dt_object + ist_offset
                    timestamp = ist_time.strftime('%Y-%m-%d %I:%M:%S %p')
                except:
                    timestamp = sent_at_str
            else:
                timestamp = 'Unknown'
            
            export_data.append({
                'Timestamp': timestamp,
                'Recipient Name': log.get('recipient_name', ''),
                'Recipient Email': log.get('recipient_email', ''),
                'Subject': log.get('subject', ''),
                'Status': log.get('status', ''),
                'Details': log.get('details', '')
            })
        
        # Create Excel file in /tmp
        timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"failed_entries_{timestamp_str}.xlsx"
        filepath = os.path.join(app.config['LOGS_FOLDER'], filename)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Create DataFrame and save
        df = pd.DataFrame(export_data)
        df.to_excel(filepath, index=False)
        
        return send_from_directory(app.config['LOGS_FOLDER'], filename, as_attachment=True)
        
    except Exception as e:
        print(f"ERROR: Error creating failed log export: {e}")
        flash(f"Error processing failed log: {e}", "error")
        return redirect(url_for('list_logs'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)


