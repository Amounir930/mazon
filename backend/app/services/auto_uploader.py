"""
Auto Uploader Service
يرفع ملفات Excel لـ Amazon Seller Central عبر PyWebView

Workflow:
1. ياخد ملف Excel
2. يفتح نافذة PyWebView بالـ session المسجلة
3. يروح لصفحة Upload Inventory
4. يرفع الملف
5. يرجع النتيجة
"""
import os
import time
import json
import tempfile
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pathlib import Path
from loguru import logger


class AutoUploader:
    """
    يرفع ملفات Excel لـ Amazon Seller Central عبر PyWebView.
    """
    
    SELLER_CENTRAL_BASE = {
        "eg": "https://sellercentral.amazon.eg",
        "sa": "https://sellercentral.amazon.sa",
        "ae": "https://sellercentral.amazon.ae",
        "uk": "https://sellercentral.amazon.co.uk",
        "us": "https://sellercentral.amazon.com",
    }
    
    @staticmethod
    def upload_file(filepath: str, country_code: str = "eg") -> Dict[str, Any]:
        """
        يرفع ملف Excel لـ Amazon.
        
        Args:
            filepath: مسار الملف
            country_code: eg, sa, ae, ...
        
        Returns:
            {
                "success": bool,
                "message": str,
                "upload_url": str
            }
        """
        try:
            base_url = AutoUploader.SELLER_CENTRAL_BASE.get(country_code, AutoUploader.SELLER_CENTRAL_BASE["eg"])
            upload_url = f"{base_url}/inventory/upload"
            
            # Create output file for result
            output_file = os.path.join(tempfile.gettempdir(), f"amzn_upload_{int(time.time())}.json")
            
            # Launch upload script
            env = os.environ.copy()
            env["AMZN_UPLOAD_URL"] = upload_url
            env["AMZN_FILE_PATH"] = filepath
            env["AMZN_OUTPUT"] = output_file
            
            import subprocess
            import sys
            
            upload_script = os.path.join(os.path.dirname(__file__), "upload_worker.py")
            
            proc = subprocess.Popen(
                [sys.executable, "-u", upload_script],
                env=env,
                creationflags=subprocess.DETACHED_PROCESS if os.name == "nt" else 0,
            )
            logger.info(f"Upload worker launched (PID={proc.pid})")
            
            # Poll for result
            max_wait = 120  # 2 minutes
            waited = 0
            
            while waited < max_wait:
                time.sleep(2)
                waited += 2
                
                if os.path.exists(output_file):
                    try:
                        time.sleep(0.5)  # Ensure file is fully written
                        with open(output_file, "r", encoding="utf-8") as f:
                            result = json.load(f)
                        logger.info(f"Upload result: {result.get('success')}")
                        return result
                    except Exception:
                        continue
            
            return {
                "success": False,
                "error": "Upload timeout",
                "upload_url": upload_url,
            }
            
        except Exception as e:
            logger.error(f"Auto-upload failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }
