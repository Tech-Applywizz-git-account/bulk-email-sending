"""
Supabase Service Module
Handles all interactions with Supabase for file storage and database operations
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Optional, Any
import uuid
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")  # Use service role key for backend operations
SUPABASE_BUCKET_NAME = os.getenv("SUPABASE_BUCKET_NAME", "email-attachments")

# Detailed logging for debugging
print("="*60)
print("SEARCH SUPABASE SERVICE INITIALIZATION")
print("="*60)
print(f"SUPABASE_URL loaded: {SUPABASE_URL is not None}")
if SUPABASE_URL:
    print(f"   URL: {SUPABASE_URL}")
else:
    print("   ERROR: SUPABASE_URL is missing!")

print(f"SUPABASE_SERVICE_KEY loaded: {SUPABASE_SERVICE_KEY is not None}")
if SUPABASE_SERVICE_KEY:
    print(f"   Key length: {len(SUPABASE_SERVICE_KEY)} chars")
    print(f"   Key starts with: {SUPABASE_SERVICE_KEY[:20]}...")
else:
    print("   ERROR: SUPABASE_SERVICE_KEY is missing!")

print(f"SUPABASE_BUCKET_NAME: {SUPABASE_BUCKET_NAME}")
print("="*60)

# Global flag to check if Supabase is properly configured and reachable
def check_supabase_reachable():
    if not SUPABASE_URL:
        return False
    try:
        import requests
        # Quick check with 2s timeout
        r = requests.get(SUPABASE_URL, timeout=2)
        return True
    except:
        print("WARNING: Supabase URL is unreachable. Falling back to local mode.")
        return False

SUPABASE_ENABLED = bool(SUPABASE_URL and SUPABASE_SERVICE_KEY)
if SUPABASE_ENABLED:
    # Check reachability once at startup
    if not check_supabase_reachable():
        SUPABASE_ENABLED = False

def is_supabase_enabled() -> bool:
    """Check if Supabase is properly configured"""
    return SUPABASE_ENABLED

if SUPABASE_ENABLED:
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        print(f"SUCCESS: Supabase client initialized successfully: {SUPABASE_URL}")
        print(f"   Client type: {type(supabase)}")
    except Exception as e:
        print(f"ERROR: Failed to initialize Supabase client: {e}")
        SUPABASE_ENABLED = False
        supabase = None
else:
    print("WARNING: Supabase not enabled or unreachable")
    supabase = None


# ==================== FILE STORAGE OPERATIONS ====================

def upload_file_to_storage(local_filepath: str, filename: str) -> Optional[str]:
    """
    Upload a file to Supabase Storage
    
    Args:
        local_filepath: Path to the local file
        filename: Name to use in storage
        
    Returns:
        Storage path if successful, None otherwise
    """
    if not is_supabase_enabled():
        print("Supabase not enabled, skipping upload")
        return None
    
    try:
        # Create organized path with year/month folders
        now = datetime.utcnow()
        storage_path = f"uploads/{now.year}/{now.month:02d}/{filename}"
        
        # Read file content
        with open(local_filepath, 'rb') as f:
            file_content = f.read()
        
        # Upload to Supabase Storage
        response = supabase.storage.from_(SUPABASE_BUCKET_NAME).upload(
            path=storage_path,
            file=file_content,
            file_options={"content-type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}
        )
        
        print(f"SUCCESS: File uploaded to Supabase Storage: {storage_path}")
        return storage_path
        
    except Exception as e:
        error_msg = f"ERROR: Error uploading to Supabase Storage: {e}"
        print(error_msg)
        # Log to our debug file too
        try:
            with open("upload_debug.log", "a") as logf:
                logf.write(f"DEBUG: STORAGE EXCEPTION: {error_msg}\n")
        except:
            pass
        return None


def download_file_from_storage(storage_path: str, local_filepath: str) -> bool:
    """
    Download a file from Supabase Storage to local filesystem
    
    Args:
        storage_path: Path in Supabase Storage
        local_filepath: Where to save the file locally
        
    Returns:
        True if successful, False otherwise
    """
    if not is_supabase_enabled():
        return False
    
    try:
        # Download from Supabase Storage
        response = supabase.storage.from_(SUPABASE_BUCKET_NAME).download(storage_path)
        
        # Save to local filesystem
        with open(local_filepath, 'wb') as f:
            f.write(response)
        
        print(f"SUCCESS: File downloaded from Supabase Storage: {storage_path}")
        return True
        
    except Exception as e:
        print(f"ERROR: Error downloading from Supabase Storage: {e}")
        return False


def delete_file_from_storage(storage_path: str) -> bool:
    """
    Delete a file from Supabase Storage
    
    Args:
        storage_path: Path in Supabase Storage
        
    Returns:
        True if successful, False otherwise
    """
    if not is_supabase_enabled():
        return False
    
    try:
        supabase.storage.from_(SUPABASE_BUCKET_NAME).remove([storage_path])
        print(f"SUCCESS: File deleted from Supabase Storage: {storage_path}")
        return True
        
    except Exception as e:
        print(f"ERROR: Error deleting from Supabase Storage: {e}")
        return False


def get_file_download_url(storage_path: str, expires_in: int = 3600) -> Optional[str]:
    """
    Get a signed URL for downloading a file
    
    Args:
        storage_path: Path in Supabase Storage
        expires_in: URL expiration time in seconds (default: 1 hour)
        
    Returns:
        Signed URL if successful, None otherwise
    """
    if not is_supabase_enabled():
        return None
    
    try:
        response = supabase.storage.from_(SUPABASE_BUCKET_NAME).create_signed_url(
            storage_path, 
            expires_in
        )
        return response.get('signedURL')
        
    except Exception as e:
        print(f"ERROR: Error creating signed URL: {e}")
        return None


# ==================== DATABASE OPERATIONS ====================

def insert_uploaded_file(filename: str, original_filename: str, storage_path: str, 
                        file_size: int, metadata: Optional[Dict] = None) -> Optional[str]:
    """
    Insert a record for an uploaded file
    
    Args:
        filename: Filename used in storage
        original_filename: Original filename from upload
        storage_path: Path in Supabase Storage
        file_size: File size in bytes
        metadata: Optional JSON metadata (parsed Excel data)
        
    Returns:
        File UUID if successful, None otherwise
    """
    if not is_supabase_enabled():
        return None
    
    try:
        data = {
            "filename": filename,
            "original_filename": original_filename,
            "file_path": storage_path,
            "file_size": file_size,
            "metadata": metadata or {}
        }
        
        response = supabase.table("uploaded_files").insert(data).execute()
        
        if response.data and len(response.data) > 0:
            file_id = response.data[0]['id']
            print(f"SUCCESS: File record inserted: {file_id}")
            return file_id
        
        # If no data returned, log the response for debugging
        with open("supabase_errors.log", "a") as f:
            f.write(f"\n[{datetime.now()}] Upload Insert Failed. Response: {response}")
        return None
        
    except Exception as e:
        error_msg = f"ERROR: Error inserting file record: {e}"
        print(error_msg)
        with open("supabase_errors.log", "a") as f:
            f.write(f"\n[{datetime.now()}] Exception: {error_msg}")
        return None


def get_all_uploaded_files() -> List[Dict]:
    """
    Retrieve all uploaded files from database
    
    Returns:
        List of file records
    """
    if not is_supabase_enabled():
        print("WARNING: get_all_uploaded_files: Supabase not enabled")
        return []
    
    try:
        print("SEARCH Querying uploaded_files table...")
        response = supabase.table("uploaded_files").select("*").order("upload_date", desc=True).execute()
        
        print(f"INFO: Query result: {len(response.data) if response.data else 0} files found")
        if response.data:
            print(f"   First file: {response.data[0].get('filename', 'N/A')}")
        
        return response.data or []
        
    except Exception as e:
        print(f"ERROR: Error fetching uploaded files: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return []


def get_file_by_id(file_id: str) -> Optional[Dict]:
    """
    Get a specific file record by ID
    
    Args:
        file_id: UUID of the file
        
    Returns:
        File record if found, None otherwise
    """
    if not is_supabase_enabled():
        return None
    
    try:
        response = supabase.table("uploaded_files").select("*").eq("id", file_id).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        
        return None
        
    except Exception as e:
        print(f"ERROR: Error fetching file: {e}")
        return None


def get_file_by_filename(filename: str) -> Optional[Dict]:
    """
    Get a file record by filename
    
    Args:
        filename: Name of the file
        
    Returns:
        File record if found, None otherwise
    """
    if not is_supabase_enabled():
        print(f"WARNING: get_file_by_filename({filename}): Supabase not enabled")
        return None
    
    try:
        print(f"SEARCH Searching for file: {filename}")
        response = supabase.table("uploaded_files").select("*").eq("filename", filename).order("upload_date", desc=True).limit(1).execute()
        
        print(f"INFO: Query response: {response}")
        print(f"   Data count: {len(response.data) if response.data else 0}")
        
        if response.data and len(response.data) > 0:
            print(f"   SUCCESS: File found: {response.data[0].get('id')}")
            return response.data[0]
        
        print(f"   ERROR: File '{filename}' not found in database")
        print(f"   This usually means:")
        print(f"      1. RLS (Row Level Security) is blocking reads")
        print(f"      2. Different Supabase project for reads vs writes")
        print(f"      3. File was deleted")
        return None
        
    except Exception as e:
        print(f"ERROR: Error fetching file by filename: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return None


def delete_file_record(file_id: str) -> bool:
    """
    Delete a file record from database
    
    Args:
        file_id: UUID of the file
        
    Returns:
        True if successful, False otherwise
    """
    if not is_supabase_enabled():
        return False
    
    try:
        supabase.table("uploaded_files").delete().eq("id", file_id).execute()
        print(f"SUCCESS: File record deleted: {file_id}")
        return True
        
    except Exception as e:
        print(f"ERROR: Error deleting file record: {e}")
        return False


# ==================== EMAIL LOG OPERATIONS ====================

def insert_email_log(batch_id: str, source_file_id: Optional[str], recipient_name: str,
                     recipient_email: str, subject: str, email_body: str,
                     status: str, details: str) -> Optional[str]:
    """
    Insert an email sending log entry
    
    Args:
        batch_id: UUID for this sending batch
        source_file_id: UUID of the source file
        recipient_name: Recipient's name
        recipient_email: Recipient's email
        subject: Email subject
        email_body: Email body content
        status: 'Success', 'Failed', 'Skipped', 'Error'
        details: Additional details or error messages
        
    Returns:
        Log entry UUID if successful, None otherwise
    """
    if not is_supabase_enabled():
        return None
    
    try:
        data = {
            "batch_id": batch_id,
            "source_file_id": source_file_id,
            "recipient_name": recipient_name,
            "recipient_email": recipient_email,
            "subject": subject,
            "email_body": email_body,
            "status": status,
            "details": details
        }
        
        response = supabase.table("email_logs").insert(data).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]['id']
        
        return None
        
    except Exception as e:
        print(f"ERROR: Error inserting email log: {e}")
        return None


def get_email_logs_by_batch(batch_id: str) -> List[Dict]:
    """
    Get all email logs for a specific batch
    
    Args:
        batch_id: UUID of the batch
        
    Returns:
        List of log entries
    """
    if not is_supabase_enabled():
        return []
    
    try:
        response = supabase.table("email_logs").select("*").eq("batch_id", batch_id).order("sent_at", desc=False).execute()
        return response.data or []
        
    except Exception as e:
        print(f"ERROR: Error fetching email logs: {e}")
        return []


def get_all_email_batches() -> List[Dict]:
    """
    Get all unique email batches with summary information
    
    Returns:
        List of batch summaries
    """
    if not is_supabase_enabled():
        return []
    
    try:
        # Get distinct batch_ids with counts and first sent_at
        response = supabase.table("email_logs").select("batch_id, sent_at, source_file_id").order("sent_at", desc=True).execute()
        
        # Group by batch_id
        batches = {}
        for log in response.data:
            batch_id = log['batch_id']
            if batch_id not in batches:
                batches[batch_id] = {
                    'batch_id': batch_id,
                    'sent_at': log['sent_at'],
                    'source_file_id': log.get('source_file_id'),
                    'count': 0
                }
            batches[batch_id]['count'] += 1
        
        return list(batches.values())
        
    except Exception as e:
        print(f"ERROR: Error fetching email batches: {e}")
        return []


# ==================== UPLOAD LOG OPERATIONS ====================

def insert_upload_log(file_id: Optional[str], action: str, status: str, 
                      details: str = "", ip_address: str = "") -> Optional[str]:
    """
    Insert an upload activity log entry
    
    Args:
        file_id: UUID of the file (if applicable)
        action: 'upload', 'delete', 'view', 'edit'
        status: 'success', 'failed'
        details: Additional details
        ip_address: IP address of the user
        
    Returns:
        Log entry UUID if successful, None otherwise
    """
    if not is_supabase_enabled():
        return None
    
    try:
        data = {
            "file_id": file_id,
            "action": action,
            "status": status,
            "details": details,
            "ip_address": ip_address
        }
        
        response = supabase.table("upload_logs").insert(data).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]['id']
        
        return None
        
    except Exception as e:
        print(f"ERROR: Error inserting upload log: {e}")
        return None


def get_upload_logs_by_file(file_id: str) -> List[Dict]:
    """
    Get all upload logs for a specific file
    
    Args:
        file_id: UUID of the file
        
    Returns:
        List of log entries
    """
    if not is_supabase_enabled():
        return []
    
    try:
        response = supabase.table("upload_logs").select("*").eq("file_id", file_id).order("created_at", desc=True).execute()
        return response.data or []
        
    except Exception as e:
        print(f"ERROR: Error fetching upload logs: {e}")
        return []
