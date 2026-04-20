from sqlalchemy.orm import Session
from app.models.setting import Setting
from loguru import logger

class CounterService:
    @staticmethod
    def get_next_serial(db: Session, key: str, prefix: str, padding: int = 4, increment: int = 1) -> str:
        """
        Get next sequential number for a specific key and increment.
        """
        setting = db.query(Setting).filter(Setting.key == key).first()
        if not setting:
            current_num = 0
            setting = Setting(key=key, value="0", description=f"Last used {key} serial")
            db.add(setting)
        else:
            try:
                current_num = int(setting.value)
            except ValueError:
                current_num = 0

        first_num = current_num + 1
        setting.value = str(current_num + increment)
        
        try:
            db.commit()
            db.refresh(setting)
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to increment counter {key}: {e}")

        return f"{prefix}{first_num:0{padding}d}"

    @staticmethod
    def get_next_model_number(db: Session, prefix: str = "AH-", padding: int = 4, increment: int = 1) -> str:
        return CounterService.get_next_serial(db, "last_model_number", prefix, padding, increment)

    @staticmethod
    def get_next_product_id(db: Session, prefix: str = "ADEL", padding: int = 6, increment: int = 1) -> str:
        return CounterService.get_next_serial(db, "last_product_id_number", prefix, padding, increment)

    @staticmethod
    def preview_next_model_number(db: Session, prefix: str = "AH-", padding: int = 4) -> str:
        setting = db.query(Setting).filter(Setting.key == "last_model_number").first()
        current_num = int(setting.value) if setting and setting.value.isdigit() else 0
        return f"{prefix}{current_num + 1:0{padding}d}"

    @staticmethod
    def preview_next_product_id(db: Session, prefix: str = "ADEL", padding: int = 6) -> str:
        setting = db.query(Setting).filter(Setting.key == "last_product_id_number").first()
        current_num = int(setting.value) if setting and setting.value.isdigit() else 0
        return f"{prefix}{current_num + 1:0{padding}d}"
