#!/usr/bin/env python3
"""
Debug script to test file upload functionality
"""

import os
from werkzeug.utils import secure_filename

def test_file_upload():
    """Test file upload functionality step by step"""
    
    print("🔍 Testing file upload functionality...")
    
    # Test 1: Check directories
    print("\n📁 Testing directories...")
    directories = ['order_upload', 'order_payment', 'order_data']
    
    for dir_name in directories:
        dir_path = os.path.join(os.getcwd(), dir_name)
        exists = os.path.exists(dir_path)
        writable = os.access(dir_path, os.W_OK) if exists else False
        permissions = oct(os.stat(dir_path).st_mode) if exists else 'N/A'
        
        print(f"   {dir_name}:")
        print(f"     Exists: {exists}")
        print(f"     Writable: {writable}")
        print(f"     Permissions: {permissions}")
        
        if not exists:
            try:
                os.makedirs(dir_path, exist_ok=True)
                print(f"     ✅ Created directory")
            except Exception as e:
                print(f"     ❌ Failed to create: {e}")
    
    # Test 2: Test filename generation
    print("\n📝 Testing filename generation...")
    tracking_code = "TEST123"
    test_filename = "test_image.jpg"
    
    secure_name = secure_filename(test_filename)
    upload_filename = f"{tracking_code}.{secure_name.rsplit('.', 1)[1].lower()}"
    
    print(f"   Original filename: {test_filename}")
    print(f"   Secure filename: {secure_name}")
    print(f"   Upload filename: {upload_filename}")
    
    # Test 3: Test path generation
    print("\n🛣️  Testing path generation...")
    order_upload_dir = os.path.join(os.getcwd(), 'order_upload')
    file_path = os.path.join('order_upload', upload_filename).replace('\\', '/')
    full_path = os.path.join(order_upload_dir, upload_filename)
    
    print(f"   Order upload dir: {order_upload_dir}")
    print(f"   Relative path: {file_path}")
    print(f"   Full path: {full_path}")
    print(f"   Full path exists: {os.path.exists(full_path)}")
    
    # Test 4: Create a test file
    print("\n📄 Creating test file...")
    try:
        test_content = "This is a test file for debugging upload functionality."
        with open(full_path, 'w') as f:
            f.write(test_content)
        
        print(f"   ✅ Test file created: {full_path}")
        print(f"   File exists: {os.path.exists(full_path)}")
        
        # Read it back
        with open(full_path, 'r') as f:
            content = f.read()
        print(f"   Content verified: {len(content)} characters")
        
    except Exception as e:
        print(f"   ❌ Failed to create test file: {e}")
    
    # Test 5: List directory contents
    print("\n📋 Directory contents after test...")
    for dir_name in directories:
        dir_path = os.path.join(os.getcwd(), dir_name)
        if os.path.exists(dir_path):
            files = os.listdir(dir_path)
            print(f"   {dir_name}: {len(files)} files")
            for file in files:
                print(f"     - {file}")
        else:
            print(f"   {dir_name}: Directory does not exist")
    
    # Cleanup
    print("\n🧹 Cleaning up test file...")
    try:
        if os.path.exists(full_path):
            os.remove(full_path)
            print(f"   ✅ Test file removed")
    except Exception as e:
        print(f"   ❌ Failed to remove test file: {e}")
    
    print("\n✅ Debug test completed!")

if __name__ == "__main__":
    test_file_upload()
