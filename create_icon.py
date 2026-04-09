"""
Icon Generator for Crazy Lister v3.0
Generates a simple .ico file using PIL/Pillow
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_icon():
    """Create a simple icon for Crazy Lister"""
    
    # Create images of different sizes for the icon
    sizes = [16, 32, 48, 64, 128, 256]
    images = []
    
    for size in sizes:
        # Create a dark background with gradient
        img = Image.new('RGBA', (size, size), (10, 10, 15, 255))
        draw = ImageDraw.Draw(img)
        
        # Draw a simple lightning bolt or "C" shape
        # Calculate proportions based on size
        padding = size // 8
        
        # Draw orange/yellow lightning bolt
        bolt_color = (255, 165, 0, 255)  # Orange
        
        # Simple lightning bolt shape
        if size >= 32:
            # Top point
            x1 = size // 2
            y1 = padding
            
            # Middle zigzag
            x2 = size // 4
            y2 = size // 3
            
            x3 = size * 3 // 4
            y3 = size // 2
            
            x4 = size // 3
            y4 = size * 2 // 3
            
            # Bottom point
            x5 = size // 2
            y5 = size - padding
            
            # Draw filled lightning bolt
            points = [(x1, y1), (x2, y2), (x3, y3), (x4, y4), (x5, y5)]
            draw.polygon(points, fill=bolt_color)
        else:
            # For small sizes, just draw a simple shape
            draw.ellipse(
                [padding, padding, size - padding, size - padding],
                fill=bolt_color
            )
        
        images.append(img)
    
    # Save as .ico
    output_path = os.path.join(os.path.dirname(__file__), 'assets', 'icon.ico')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    images[0].save(
        output_path,
        format='ICO',
        sizes=[(img.width, img.height) for img in images]
    )
    
    print(f"✅ Icon created: {output_path}")
    return output_path

if __name__ == "__main__":
    try:
        create_icon()
    except ImportError:
        print("❌ Pillow not installed. Install with: pip install Pillow")
        print("\nAlternatively, you can:")
        print("1. Download a .ico file from https://icoconvert.com/")
        print("2. Place it in assets/icon.ico")
    except Exception as e:
        print(f"❌ Error creating icon: {e}")
