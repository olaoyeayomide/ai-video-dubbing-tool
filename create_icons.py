# Create simple icon placeholders for the Chrome extension
from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size, filename):
    # Create image with gradient background
    img = Image.new('RGBA', (size, size), (102, 126, 234, 255))
    draw = ImageDraw.Draw(img)
    
    # Add simple RTD text
    try:
        # Try to use a built-in font
        font_size = size // 4
        font = ImageFont.load_default()
    except:
        font = None
    
    # Draw RTD text
    text = "RTD"
    if font:
        # Get text size
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Center the text
        x = (size - text_width) // 2
        y = (size - text_height) // 2
        
        draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)
    else:
        # Fallback: draw simple shape
        draw.ellipse([size//4, size//4, 3*size//4, 3*size//4], 
                    fill=(255, 255, 255, 255))
    
    # Save the image
    img.save(filename, 'PNG')
    print(f"Created {filename} ({size}x{size})")

# Create icons directory
os.makedirs('/workspace/code/realtime_dubbing/extension/icons', exist_ok=True)

# Create all required icon sizes
icon_sizes = [(16, 'icon-16.png'), (48, 'icon-48.png'), (128, 'icon-128.png')]

for size, filename in icon_sizes:
    filepath = f'/workspace/code/realtime_dubbing/extension/icons/{filename}'
    create_icon(size, filepath)

print("All extension icons created successfully!")