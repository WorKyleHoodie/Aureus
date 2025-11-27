import requests
import json
import os
from datetime import datetime

# define paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

def get_latest_hiring_thread_id():
    """find the latest 'Who is hiring' thread id"""
    url = "https://hn.algolia.com/api/v1/search_by_date"
    params = {
        "query": "Ask HN: Who is hiring?",
        "tags": "story,author_whoishiring",
        "hitsPerPage": 1
    }
    try:
        print("🔍 Searching for latest hiring thread...")
        response = requests.get(url, params=params)
        data = response.json()
        if data['hits']:
            latest = data['hits'][0]
            return latest['objectID'], latest['title']
    except Exception as e:
        print(f"❌ Search error: {e}")
    return None, None

def fetch_comments(thread_id, limit=20):
    """fetch comments for a given thread id"""
    print(f"🚀 Start fetching comments for thread {thread_id}...")

    # 1. fetch thread details to get comment ids
    item_url = f"https://hacker-news.firebaseio.com/v0/item/{thread_id}.json"
    try:
        item_data = requests.get(item_url).json()
        comment_ids = item_data.get('kids', [])
    except Exception as e:
        print(f"❌ Fetching thread details failed: {e}")
        return []

    print(f"📦 Found {len(comment_ids)} Comments，fetching first {limit} for testing...")

    comments = []
    for index, cid in enumerate(comment_ids[:limit]):
        try:
            c_url = f"https://hacker-news.firebaseio.com/v0/item/{cid}.json"
            c_data = requests.get(c_url).json()

            # simple clean: must have text and not deleted
            if c_data and 'text' in c_data and not c_data.get('deleted'):
                comments.append({
                    "id": c_data['id'],
                    "user": c_data.get('by', 'unknown'),
                    "time": datetime.fromtimestamp(c_data['time']).isoformat(),
                    "content": c_data['text']
                })
                print(f"  [{index+1}/{limit}] ✅ Comment fetched: {c_data['id']}")
        except Exception as e:
            print(f"  [{index+1}/{limit}] ⚠️ Skipped: {e}")

    return comments

def save_raw_data(data, filename="raw_jobs.json"):
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Data saved to: {filepath}")

if __name__ == "__main__":
    tid, title = get_latest_hiring_thread_id()
    if tid:
        print(f"🎯 Target thread: {title} (ID: {tid})")

        raw_data = fetch_comments(tid, limit=20)

        if raw_data:
            save_raw_data(raw_data)
            print(f"🎉 Successfully fetched {len(raw_data)} raw comments! Phase 1 completed half!")
        else:
            print("⚠️ No valid comments fetched.")
    else:
        print("⚠️ No hiring thread found.")
