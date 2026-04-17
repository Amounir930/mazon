import os
import psutil

for proc in psutil.process_iter(['pid', 'name', 'cwd']):
    try:
        if 'python' in proc.info['name'].lower():
            print(f"PID: {proc.info['pid']}, Name: {proc.info['name']}, CWD: {proc.info['cwd']}")
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        pass
