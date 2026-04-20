import os
import json
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# ✅ CORRECT PATHS for the actual AppData directory
APP_DATA_DIR = Path(os.getenv("APPDATA")) / "CrazyLister"
COUNTER_FILE = APP_DATA_DIR / "persistent_counters.json"
DB_PATH = APP_DATA_DIR / "crazy_lister.db"

def initialize():
    print(f"🚀 Targeted Directory: {APP_DATA_DIR}")
    
    # Target value: 100 (so the next one generated is 101)
    target_val = 100
    
    # 1. Update Persistent JSON File
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "last_model_number": target_val,
        "last_product_id_number": target_val,
        "last_sku_serial": target_val
    }
    with open(COUNTER_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    print(f"✅ Persistent file updated at: {COUNTER_FILE}")

    # 2. Update the REAL Database
    if DB_PATH.exists():
        try:
            engine = create_engine(f"sqlite:///{DB_PATH}")
            Session = sessionmaker(bind=engine)
            session = Session()
            
            # Update or Insert Settings
            keys = ["last_model_number", "last_product_id_number", "last_sku_serial"]
            for key in keys:
                # First check if table exists
                session.execute(text(
                    "INSERT OR REPLACE INTO settings (key, value, description) VALUES (:key, :value, :desc)"
                ), {"key": key, "value": str(target_val), "desc": f"Last used {key} serial"})
            
            session.commit()
            print(f"✅ Database counters updated at: {DB_PATH}")
            session.close()
        except Exception as e:
            print(f"⚠️ Could not update database: {e}")
    else:
        print(f"⚠️ Database not found at {DB_PATH}. It will be created when the app starts.")

    print("\n🎉 Done! Now REFRESH the Add Product page. The next product will start with 101.")

if __name__ == "__main__":
    initialize()
