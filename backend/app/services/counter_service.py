import os
import json
from pathlib import Path
from sqlalchemy.orm import Session
from app.models.setting import Setting
from loguru import logger

class CounterService:
    # Path for persistent storage that survives DB deletion
    # Points to C:\Users\USER\AppData\Roaming\CrazyLister\persistent_counters.json on Windows
    COUNTER_FILE = Path(os.getenv("APPDATA", str(Path.home()))) / "CrazyLister" / "persistent_counters.json"

    @staticmethod
    def _ensure_dir():
        """Ensure the storage directory exists"""
        CounterService.COUNTER_FILE.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _load_counters() -> dict:
        """Load counters from persistent file"""
        if CounterService.COUNTER_FILE.exists():
            try:
                with open(CounterService.COUNTER_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load persistent counters: {e}")
        return {}

    @staticmethod
    def _save_counters(counters: dict):
        """Save counters to persistent file"""
        try:
            CounterService._ensure_dir()
            with open(CounterService.COUNTER_FILE, 'w', encoding='utf-8') as f:
                json.dump(counters, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save persistent counters: {e}")

    @staticmethod
    def get_next_serial(db: Session, key: str, prefix: str, padding: int = 4, increment: int = 1) -> str:
        """
        Get next sequential number using both File and DB for maximum persistence.
        """
        # 1. Try to get from persistent file first
        persistent_data = CounterService._load_counters()
        file_val = persistent_data.get(key)
        
        # 2. Try to get from DB
        setting = db.query(Setting).filter(Setting.key == key).first()
        db_val = int(setting.value) if setting and setting.value.isdigit() else 0
        
        # 3. Use the HIGHEST value between File and DB to prevent duplicates
        current_num = max(int(file_val) if file_val is not None else 0, db_val)
        
        next_num = current_num + 1
        new_val = current_num + increment
        
        # 4. Update DB
        if not setting:
            setting = Setting(key=key, value=str(new_val), description=f"Last used {key} serial")
            db.add(setting)
        else:
            setting.value = str(new_val)
            
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"DB Counter update failed: {e}")

        # 5. Update Persistent File (The most important step)
        persistent_data[key] = new_val
        CounterService._save_counters(persistent_data)
        
        logger.info(f"🔢 Counter '{key}' incremented: {current_num} -> {new_val} (Saved to File & DB)")
        
        return f"{prefix}{next_num:0{padding}d}"

    @staticmethod
    def get_next_model_number(db: Session, prefix: str = "AH-", padding: int = 4, increment: int = 1) -> str:
        return CounterService.get_next_serial(db, "last_model_number", prefix, padding, increment)

    @staticmethod
    def get_next_product_id(db: Session, prefix: str = "ADEL", padding: int = 6, increment: int = 1) -> str:
        return CounterService.get_next_serial(db, "last_product_id_number", prefix, padding, increment)

    @staticmethod
    def get_next_sku_serial(db: Session, prefix: str = "SKU-V1-", padding: int = 3, increment: int = 1) -> str:
        return CounterService.get_next_serial(db, "last_sku_serial", prefix, padding, increment)

    @staticmethod
    def preview_next_model_number(db: Session, prefix: str = "AH-", padding: int = 4) -> str:
        persistent_data = CounterService._load_counters()
        file_val = persistent_data.get("last_model_number", 0)
        setting = db.query(Setting).filter(Setting.key == "last_model_number").first()
        db_val = int(setting.value) if setting and setting.value.isdigit() else 0
        current_num = max(int(file_val), db_val)
        return f"{prefix}{current_num + 1:0{padding}d}"

    @staticmethod
    def preview_next_product_id(db: Session, prefix: str = "ADEL", padding: int = 6) -> str:
        persistent_data = CounterService._load_counters()
        file_val = persistent_data.get("last_product_id_number", 0)
        setting = db.query(Setting).filter(Setting.key == "last_product_id_number").first()
        db_val = int(setting.value) if setting and setting.value.isdigit() else 0
        current_num = max(int(file_val), db_val)
        return f"{prefix}{current_num + 1:0{padding}d}"

    @staticmethod
    def preview_next_sku_serial(db: Session, prefix: str = "SKU-V1-", padding: int = 3) -> str:
        persistent_data = CounterService._load_counters()
        file_val = persistent_data.get("last_sku_serial", 0)
        setting = db.query(Setting).filter(Setting.key == "last_sku_serial").first()
        db_val = int(setting.value) if setting and setting.value.isdigit() else 0
        current_num = max(int(file_val), db_val)
        return f"{prefix}{current_num + 1:0{padding}d}"
