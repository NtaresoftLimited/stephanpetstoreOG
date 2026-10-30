
from PIL import Image, ImageDraw

def create_paw_image(filename="paw_watermark.png", size=(500, 500), color=(107, 78, 61, 50)): # Updated to use brand color #6b4e3d with low opacity
    # Create transparent image
    img = Image.new('RGBA', size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Paw Pad coordinates (center)
    center_x, center_y = size[0] // 2, size[1] // 2 + 50
    pad_idx = [
        (center_x - 60, center_y - 20),
        (center_x + 60, center_y - 20),
        (center_x, center_y + 80),
        (center_x - 90, center_y + 30),
        (center_x + 90, center_y + 30)
    ]
    
    # Main pad - simplify as a large oval/circle combo
    draw.ellipse([center_x - 70, center_y - 30, center_x + 70, center_y + 60], fill=color)
    
    # Toes
    toe_offsets = [
        (-90, -90, 40),
        (-35, -130, 45),
        (35, -130, 45),
        (90, -90, 40)
    ]
    
    for ox, oy, radius in toe_offsets:
        x = center_x + ox
        y = center_y + oy
        draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=color)
        
    img.save(filename, "PNG")
    print(f"Generated {filename}")

if __name__ == "__main__":
    create_paw_image()
