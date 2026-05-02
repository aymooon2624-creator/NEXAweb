#!/usr/bin/env python3
"""
Script to find missing files and check database paths
"""

import os
import sys
from database import init_mongo

def check_database_paths():
    """Check all file paths in database"""
    from pymongo import MongoClient
    
    # Try to connect to MongoDB Atlas (replace with your actual URI)
    try:
        # You need to replace this with your actual MongoDB Atlas URI
        mongo = MongoClient("mongodb+srv://username:password@cluster.mongodb.net/nexaweb?retryWrites=true&w=majority")
        orders = list(mongo.nexaweb.orders.find())
        print("✅ Connected to MongoDB Atlas")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB Atlas: {e}")
        # Fallback to local MongoDB
        mongo = MongoClient("mongodb://localhost:27017/")
        orders = list(mongo.nexaweb.orders.find())
        print("🔄 Connected to local MongoDB")
    
    missing_files = []
    existing_files = []
    
    for order in orders:
        tracking_code = order.get('tracking_code', 'Unknown')
        file_path = order.get('file_path', '')
        deposit_receipt_path = order.get('deposit_receipt_path', '')
        final_receipt_path = order.get('final_receipt_path', '')
        
        print(f"\n📋 Order: {tracking_code}")
        print(f"   file_path: {file_path}")
        print(f"   deposit_receipt_path: {deposit_receipt_path}")
        print(f"   final_receipt_path: {final_receipt_path}")
        
        # Check each file path
        for path_name, path_value in [
            ('file_path', file_path),
            ('deposit_receipt_path', deposit_receipt_path),
            ('final_receipt_path', final_receipt_path)
        ]:
            if path_value:
                full_path = os.path.join(os.getcwd(), path_value.replace('/', os.sep))
                if os.path.exists(full_path):
                    existing_files.append((tracking_code, path_name, path_value))
                    print(f"   ✅ {path_name}: EXISTS")
                else:
                    missing_files.append((tracking_code, path_name, path_value))
                    print(f"   ❌ {path_name}: MISSING")
    
    print(f"\n📊 Summary:")
    print(f"   Total orders: {len(orders)}")
    print(f"   Existing files: {len(existing_files)}")
    print(f"   Missing files: {len(missing_files)}")
    
    if missing_files:
        print(f"\n❌ Missing files:")
        for tracking_code, path_name, path_value in missing_files:
            print(f"   {tracking_code}: {path_name} -> {path_value}")
    
    return missing_files, existing_files

def find_old_structure_files():
    """Find files in old directory structure"""
    base_dir = os.getcwd()
    
    old_structure_files = []
    
    # Check old structure
    for subdir in ['order_upload', 'order_payment', 'order_data']:
        subdir_path = os.path.join(base_dir, subdir)
        if os.path.exists(subdir_path):
            for root, dirs, files in os.walk(subdir_path):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, base_dir)
                    old_structure_files.append(rel_path)
                    print(f"📁 Found file: {rel_path}")
    
    return old_structure_files

if __name__ == "__main__":
    print("🔍 Checking database file paths...")
    missing, existing = check_database_paths()
    
    print(f"\n🔍 Checking old file structure...")
    old_files = find_old_structure_files()
    
    print(f"\n🎯 Analysis complete!")
    print(f"   Missing files in DB: {len(missing)}")
    print(f"   Existing files in DB: {len(existing)}")
    print(f"   Files in old structure: {len(old_files)}")
