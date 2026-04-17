from PIL import Image
import os
import sys

def convert_to_png(source_path, target_path):
    try:
        img = Image.open(source_path)
        # Ensure it's square for best results
        width, height = img.size
        size = min(width, height)
        left = (width - size) / 2
        top = (height - size) / 2
        right = (width + size) / 2
        bottom = (height + size) / 2
        img = img.crop((left, top, right, bottom))
        
        img.save(target_path, format='PNG')
        print(f"Successfully converted {source_path} to {target_path}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    source = r"C:\Users\Dell\.gemini\antigravity\brain\31a189a7-aae5-4bc3-aa4d-2b6a39823f97\app_logo_source_1776456513048.png"
    target = r"c:\Users\Dell\Desktop\learn\amazon\assets\icon.png"
    convert_to_png(source, target)
