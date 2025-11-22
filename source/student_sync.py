"""
Sync student_keys.csv from OneDrive to local cache.
Keeps a local copy for offline work and syncs when online.

This file can be shared between repos - it finds the local repo root automatically.
"""
import os
import shutil
from pathlib import Path
from datetime import datetime
import hashlib

# Primary location (OneDrive) - updated path
ONEDRIVE_PATH = Path.home() / "Library/CloudStorage/OneDrive-MontclairPublicSchools/PhysSetAutomation/processed/portfolios/student_keys.csv"

# Find the repo root (where this script's parent's parent is)
REPO_ROOT = Path(__file__).parent.parent

# Local cache location (git-ignored)
LOCAL_CACHE = REPO_ROOT / "annual_setup/.student_keys_cache.csv"

# Current location used by code
CURRENT_LOCATION = REPO_ROOT / "annual_setup/student_keys.csv"

def get_file_hash(filepath: Path) -> str:
    """Get MD5 hash of file for comparison."""
    if not filepath.exists():
        return None
    with open(filepath, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def sync_student_data(force: bool = False, direction: str = "from_cloud") -> dict:
    """
    Sync student data between OneDrive and local.
    
    Args:
        force: If True, sync even if files are identical
        direction: "from_cloud" (default) or "to_cloud"
    
    Returns:
        dict with sync status information
    """
    result = {
        "synced": False,
        "source": None,
        "destination": None,
        "timestamp": datetime.now().isoformat(),
        "message": ""
    }
    
    # Check if OneDrive is available
    onedrive_available = ONEDRIVE_PATH.exists()
    
    if direction == "from_cloud":
        source = ONEDRIVE_PATH
        dest = CURRENT_LOCATION
        result["source"] = "OneDrive"
        result["destination"] = "Local"
        
        if not onedrive_available:
            # Use cache if OneDrive not available
            if LOCAL_CACHE.exists():
                source = LOCAL_CACHE
                result["source"] = "Cache"
                result["message"] = "OneDrive unavailable, using cached copy"
            else:
                result["message"] = "OneDrive unavailable and no cache exists"
                return result
    
    else:  # to_cloud
        source = CURRENT_LOCATION
        dest = ONEDRIVE_PATH
        result["source"] = "Local"
        result["destination"] = "OneDrive"
        
        if not onedrive_available:
            result["message"] = "OneDrive not available, cannot sync to cloud"
            return result
    
    # Check if sync is needed
    source_hash = get_file_hash(source)
    dest_hash = get_file_hash(dest)
    
    if not force and source_hash == dest_hash:
        result["message"] = "Files are identical, no sync needed"
        return result
    
    # Perform sync
    try:
        # Ensure destination directory exists
        dest.parent.mkdir(parents=True, exist_ok=True)
        
        # Backup existing destination if it exists
        if dest.exists():
            backup_path = dest.with_suffix('.csv.backup')
            shutil.copy2(dest, backup_path)
        
        # Copy file
        shutil.copy2(source, dest)
        
        # Update cache if syncing from cloud
        if direction == "from_cloud" and onedrive_available:
            LOCAL_CACHE.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, LOCAL_CACHE)
        
        result["synced"] = True
        result["message"] = f"Successfully synced from {result['source']} to {result['destination']}"
        
    except Exception as e:
        result["message"] = f"Error during sync: {str(e)}"
    
    return result

def get_student_file_path() -> Path:
    """
    Get the path to the student data file, syncing if necessary.
    This is the function your code should call.
    """
    # Try to sync from cloud
    sync_result = sync_student_data()
    
    if not CURRENT_LOCATION.exists():
        raise FileNotFoundError(
            f"Student data not found. Sync status: {sync_result['message']}"
        )
    
    return CURRENT_LOCATION

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Sync student data")
    parser.add_argument(
        "--to-cloud",
        action="store_true",
        help="Sync from local to OneDrive (default is from OneDrive to local)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force sync even if files are identical"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show sync status without syncing"
    )
    
    args = parser.parse_args()
    
    if args.status:
        print(f"Repository root: {REPO_ROOT}")
        print(f"OneDrive path: {ONEDRIVE_PATH}")
        print(f"OneDrive available: {ONEDRIVE_PATH.exists()}")
        print(f"Local cache: {LOCAL_CACHE}")
        print(f"Cache exists: {LOCAL_CACHE.exists()}")
        print(f"Current location: {CURRENT_LOCATION}")
        print(f"Current exists: {CURRENT_LOCATION.exists()}")
        
        if ONEDRIVE_PATH.exists() and CURRENT_LOCATION.exists():
            onedrive_hash = get_file_hash(ONEDRIVE_PATH)
            local_hash = get_file_hash(CURRENT_LOCATION)
            print(f"\nFiles identical: {onedrive_hash == local_hash}")
    else:
        direction = "to_cloud" if args.to_cloud else "from_cloud"
        result = sync_student_data(force=args.force, direction=direction)
        
        print(f"Sync result: {result['message']}")
        if result['synced']:
            print(f"  From: {result['source']}")
            print(f"  To: {result['destination']}")
            print(f"  Time: {result['timestamp']}")
