#!/usr/bin/env python3
"""
Script to update original_filename field to tracking_code for all orders
"""

from pymongo import MongoClient

def update_original_filename_to_tracking_code():
    """Update original_filename field to tracking_code for all orders"""
    
    try:
        # Connect to MongoDB Atlas (replace with your actual URI)
        mongo = MongoClient("mongodb+srv://username:password@cluster.mongodb.net/nexaweb?retryWrites=true&w=majority")
        db = mongo.nexaweb
        orders_collection = db.orders
        
        print("🔍 Connected to MongoDB Atlas")
        
        # Get all orders
        orders = list(orders_collection.find())
        print(f"📊 Found {len(orders)} orders")
        
        updated_count = 0
        
        for order in orders:
            tracking_code = order.get('tracking_code', 'Unknown')
            order_id = order.get('_id')
            current_original_filename = order.get('original_filename', '')
            
            # Update original_filename to tracking_code
            if current_original_filename != tracking_code:
                print(f"🔄 Updating order: {tracking_code}")
                print(f"   Current original_filename: {current_original_filename}")
                print(f"   New original_filename: {tracking_code}")
                
                result = orders_collection.update_one(
                    {'_id': order_id},
                    {'$set': {'original_filename': tracking_code}}
                )
                
                if result.modified_count > 0:
                    updated_count += 1
                    print(f"   ✅ Updated successfully")
                else:
                    print(f"   ❌ Update failed")
            else:
                print(f"ℹ️  original_filename already correct for order: {tracking_code}")
        
        print(f"\n📊 Summary:")
        print(f"   Total orders: {len(orders)}")
        print(f"   Orders updated: {updated_count}")
        print(f"   Orders already correct: {len(orders) - updated_count}")
        
        mongo.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🔄 Starting update of original_filename to tracking_code...")
    update_original_filename_to_tracking_code()
    print("✅ Process completed!")
