import os
from supabase import create_client
from dotenv import load_dotenv
load_dotenv()

url = os.environ["SUPABASE_URL"]
key = os.environ["SUPABASE_KEY"]
supabase = create_client(url, key)

# Test insert for chat_history (match your actual table columns)
data = {
    "user_id": "dathuynh",
    "workflow_id": "test_workflow",
    "message": "Hello, world!",
    "sender": "system"
}
resp = supabase.table("chat_history").insert(data).execute()
print(resp)