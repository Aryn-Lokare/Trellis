import os
from dotenv import load_dotenv
from extractor import get_supabase_client

load_dotenv()
supabase = get_supabase_client()

print("Cleaning database...")
try:
    # Delete from child tables first to respect foreign keys
    print("Deleting from relationships...")
    supabase.table("relationships").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    
    print("Deleting from entities...")
    supabase.table("entities").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    
    print("Deleting from documents...")
    supabase.table("documents").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    
    print("Database cleared successfully!")
except Exception as e:
    print(f"Failed to clear database: {str(e)}")
