"""
Test Azure Connection - Verify your setup
"""

import os
from dotenv import load_dotenv

load_dotenv()

def print_header(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def test_env_variables():
    print_header("1. Checking Environment Variables")
    
    storage_conn = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    cosmos_endpoint = os.getenv("COSMOS_ENDPOINT")
    cosmos_key = os.getenv("COSMOS_KEY")
    
    if storage_conn and "DefaultEndpointsProtocol" in storage_conn:
        print("✅ Storage connection string loaded")
    else:
        print("❌ Storage connection string missing")
        return False
    
    if cosmos_endpoint and cosmos_endpoint.startswith("https://"):
        print("✅ Cosmos DB endpoint loaded")
    else:
        print("❌ Cosmos DB endpoint missing")
        return False
    
    if cosmos_key and len(cosmos_key) > 50:
        print("✅ Cosmos DB key loaded")
    else:
        print("❌ Cosmos DB key missing")
        return False
    
    return True

def test_blob_storage():
    print_header("2. Testing Blob Storage")
    
    try:
        from azure.storage.blob import BlobServiceClient
        
        connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME")
        
        blob_service = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service.get_container_client(container_name)
        properties = container_client.get_container_properties()
        
        print(f"✅ Connected to Storage: {blob_service.account_name}")
        print(f"✅ Container '{container_name}' accessible")
        return True
        
    except Exception as e:
        print(f"❌ Blob Storage failed: {str(e)}")
        return False

def test_cosmos_db():
    print_header("3. Testing Cosmos DB")
    
    try:
        from azure.cosmos import CosmosClient
        
        endpoint = os.getenv("COSMOS_ENDPOINT")
        key = os.getenv("COSMOS_KEY")
        database_name = os.getenv("COSMOS_DATABASE_NAME")
        container_name = os.getenv("COSMOS_CONTAINER_NAME")
        
        client = CosmosClient(endpoint, key)
        database = client.get_database_client(database_name)
        container = database.get_container_client(container_name)
        
        query = "SELECT VALUE COUNT(1) FROM c"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        count = items[0] if items else 0
        
        print(f"✅ Connected to Cosmos DB")
        print(f"✅ Database: {database_name}")
        print(f"✅ Container: {container_name}")
        print(f"✅ Documents: {count}")
        return True
        
    except Exception as e:
        print(f"❌ Cosmos DB failed: {str(e)}")
        return False

def create_sample_data():
    print_header("4. Creating Sample Data")
    
    try:
        from azure.cosmos import CosmosClient
        from datetime import datetime
        
        endpoint = os.getenv("COSMOS_ENDPOINT")
        key = os.getenv("COSMOS_KEY")
        database_name = os.getenv("COSMOS_DATABASE_NAME")
        container_name = os.getenv("COSMOS_CONTAINER_NAME")
        
        client = CosmosClient(endpoint, key)
        database = client.get_database_client(database_name)
        container = database.get_container_client(container_name)
        
        sample_expenses = [
            {
                "id": "exp_001",
                "amount": 450.00,
                "category": "Food",
                "description": "Grocery shopping",
                "merchant": "Big Bazaar",
                "date": "2025-10-20",
                "created_at": datetime.now().isoformat()
            },
            {
                "id": "exp_002",
                "amount": 200.00,
                "category": "Transport",
                "description": "Uber ride",
                "merchant": "Uber",
                "date": "2025-10-21",
                "created_at": datetime.now().isoformat()
            },
            {
                "id": "exp_003",
                "amount": 1500.00,
                "category": "Shopping",
                "description": "New shoes",
                "merchant": "Nike Store",
                "date": "2025-10-22",
                "created_at": datetime.now().isoformat()
            }
        ]
        
        created = 0
        for expense in sample_expenses:
            try:
                container.create_item(body=expense)
                print(f"✅ Created: {expense['description']} - ₹{expense['amount']}")
                created += 1
            except Exception as e:
                if "Conflict" in str(e):
                    print(f"ℹ️  Exists: {expense['description']}")
        
        print(f"\n✅ Created {created} new expenses!")
        return True
        
    except Exception as e:
        print(f"❌ Failed: {str(e)}")
        return False

def main():
    print("\n" + "🧪" * 30)
    print("   AZURE EXPENSE TRACKER - CONNECTION TEST")
    print("🧪" * 30)
    
    if not os.path.exists('.env'):
        print("\n❌ ERROR: .env file not found!")
        return
    
    env_ok = test_env_variables()
    if not env_ok:
        print("\n⚠️  Fix .env file first!")
        return
    
    blob_ok = test_blob_storage()
    cosmos_ok = test_cosmos_db()
    
    print_header("📊 TEST SUMMARY")
    print(f"Environment:  {'✅ PASS' if env_ok else '❌ FAIL'}")
    print(f"Blob Storage: {'✅ PASS' if blob_ok else '❌ FAIL'}")
    print(f"Cosmos DB:    {'✅ PASS' if cosmos_ok else '❌ FAIL'}")
    
    if env_ok and blob_ok and cosmos_ok:
        print("\n🎉 ALL TESTS PASSED!")
        
        response = input("\nCreate sample data? (y/n): ")
        if response.lower() in ['y', 'yes']:
            create_sample_data()
        
        print("\n" + "=" * 60)
        print("🚀 NEXT: Run the Flask app")
        print("   python app.py")
        print("=" * 60)
    else:
        print("\n⚠️  Fix errors above before continuing")

if __name__ == "__main__":
    main()