#!/usr/bin/env python3
"""
Script to migrate old file structure to new naming convention
"""

import os
import shutil
from datetime import datetime

def migrate_old_structure():
    """Migrate files from old structure to new naming convention"""
    
    base_dir = os.getcwd()
    migrated_files = []
    failed_migrations = []
    
    # Define old and new structures
    directories = {
        'order_upload': 'order_upload',
        'order_payment': 'order_payment', 
        'order_data': 'order_data'
    }
    
    print("🔄 Starting migration of old file structure...")
    
    for old_dir, new_dir in directories.items():
        old_path = os.path.join(base_dir, old_dir)
        
        if not os.path.exists(old_path):
            print(f"📁 Directory {old_dir} does not exist")
            continue
            
        print(f"\n📂 Processing {old_dir}...")
        
        # Walk through old structure
        for root, dirs, files in os.walk(old_path):
            for file in files:
                old_file_path = os.path.join(root, file)
                rel_path = os.path.relpath(old_file_path, base_dir)
                
                # Extract tracking code from path
                path_parts = rel_path.split(os.sep)
                if len(path_parts) >= 2:
                    tracking_code = path_parts[1]
                    
                    # Determine new filename
                    if old_dir == 'order_data':
                        # For order_data, use tracking_code.txt
                        new_filename = f"{tracking_code}.txt"
                    elif old_dir == 'order_payment':
                        # For order_payment, use tracking_code.jpg
                        new_filename = f"{tracking_code}.jpg"
                    elif old_dir == 'order_upload':
                        # For order_upload, preserve extension
                        file_ext = file.rsplit('.', 1)[1].lower() if '.' in file else 'jpg'
                        new_filename = f"{tracking_code}.{file_ext}"
                    else:
                        continue
                    
                    new_file_path = os.path.join(base_dir, new_dir, new_filename)
                    
                    # Check if new file already exists
                    if os.path.exists(new_file_path):
                        print(f"⚠️  File already exists: {new_filename}")
                        continue
                    
                    try:
                        # Copy file to new location
                        shutil.copy2(old_file_path, new_file_path)
                        migrated_files.append((rel_path, f"{new_dir}/{new_filename}"))
                        print(f"✅ Migrated: {rel_path} -> {new_dir}/{new_filename}")
                        
                    except Exception as e:
                        failed_migrations.append((rel_path, str(e)))
                        print(f"❌ Failed to migrate {rel_path}: {e}")
    
    print(f"\n📊 Migration Summary:")
    print(f"   Successfully migrated: {len(migrated_files)}")
    print(f"   Failed migrations: {len(failed_migrations)}")
    
    if migrated_files:
        print(f"\n✅ Migrated files:")
        for old_path, new_path in migrated_files:
            print(f"   {old_path} -> {new_path}")
    
    if failed_migrations:
        print(f"\n❌ Failed migrations:")
        for old_path, error in failed_migrations:
            print(f"   {old_path}: {error}")
    
    return migrated_files, failed_migrations

def find_all_files():
    """Find all files in project directory"""
    base_dir = os.getcwd()
    all_files = []
    
    for root, dirs, files in os.walk(base_dir):
        # Skip certain directories
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.windsurf']]
        
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, base_dir)
            all_files.append(rel_path)
    
    return all_files

if __name__ == "__main__":
    print("🔍 Finding all files in project...")
    all_files = find_all_files()
    
    # Filter for relevant files
    relevant_files = [f for f in all_files if any(x in f for x in ['order_', 'UDSFM4EH', 'W6UTV2VU', 'FP5VL8XX', 'XSAAUMHS'])]
    
    print(f"\n📁 Found {len(relevant_files)} relevant files:")
    for file in relevant_files:
        print(f"   {file}")
    
    if relevant_files:
        print(f"\n🔄 Starting migration...")
        migrated, failed = migrate_old_structure()
    else:
        print(f"\nℹ️  No relevant files found for migration")
