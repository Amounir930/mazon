from sqlalchemy.orm import Session
from app.models.setting import Setting
from loguru import logger

class CounterService:
    @staticmethod
    def get_next_model_number(db: Session, prefix: str = "AH-", padding: int = 4, increment: int = 1) -> str:
        """
        Get the starting sequential model number and increment the counter by 'increment'.
        Returns the FIRST number in the sequence.
        """
        # Get or create the setting
        counter_key = "last_model_number"
        setting = db.query(Setting).filter(Setting.key == counter_key).first()

        if not setting:
            current_num = 0
            setting = Setting(key=counter_key, value="0", description="Last used model number serial")
            db.add(setting)
        else:
            try:
                current_num = int(setting.value)
            except ValueError:
                current_num = 0

        # The number to return is current_num + 1
        first_num = current_num + 1
        
        # Increment global counter by the requested amount
        setting.value = str(current_num + increment)
        
        try:
            db.commit()
            db.refresh(setting)
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to increment model counter: {e}")

        return f"{prefix}{first_num:0{padding}d}"

    @staticmethod
    def preview_next_model_number(db: Session, prefix: str = "AH-", padding: int = 4) -> str:
        """Get the next number WITHOUT incrementing it (for preview)"""
        setting = db.query(Setting).filter(Setting.key == "last_model_number").first()
        current_num = int(setting.value) if setting and setting.value.isdigit() else 0
        return f"{prefix}{current_num + 1:0{padding}d}"
