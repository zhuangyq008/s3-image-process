from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

def add_watermark(image_data, text, t=100, g='se', x=10, y=10, voffset=0, fill=0, padx=0, pady=0):
    # Open the image
    image = Image.open(BytesIO(image_data))
    
    # Create a transparent layer for the watermark
    watermark = Image.new('RGBA', image.size, (0,0,0,0))
    draw = ImageDraw.Draw(watermark)
    
    # Load a font (you may need to specify a font file path)
    font = ImageFont.load_default()
    
    # Calculate text size using textbbox
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    text_width = right - left
    text_height = bottom - top
    
    # Calculate position
    position = {
        'nw': (x, y),
        'north': ((image.width - text_width) // 2, y),
        'ne': (image.width - text_width - x, y),
        'west': (x, (image.height - text_height) // 2),
        'center': ((image.width - text_width) // 2, (image.height - text_height) // 2),
        'east': (image.width - text_width - x, (image.height - text_height) // 2),
        'sw': (x, image.height - text_height - y),
        'south': ((image.width - text_width) // 2, image.height - text_height - y),
        'se': (image.width - text_width - x, image.height - text_height - y)
    }.get(g, (image.width - text_width - x, image.height - text_height - y))  # Default to 'se'
    
    # Adjust vertical position if needed
    if g in ['west', 'center', 'east']:
        position = (position[0], position[1] + voffset)
    
    # Draw the text
    draw.text(position, text, font=font, fill=(255,255,255,int(t * 2.55)))
    
    # Composite the watermark with the image
    output = Image.alpha_composite(image.convert('RGBA'), watermark)
    
    # Handle fill option
    if fill == 1:
        for i in range(0, image.width, text_width + padx):
            for j in range(0, image.height, text_height + pady):
                draw.text((i, j), text, font=font, fill=(255,255,255,int(t * 2.55)))
        output = Image.alpha_composite(output, watermark)
    
    # Convert back to RGB (removing alpha channel)
    output = output.convert('RGB')
    
    # Save the image to a BytesIO object
    img_byte_arr = BytesIO()
    output.save(img_byte_arr, format='JPEG')
    img_byte_arr = img_byte_arr.getvalue()
    
    return img_byte_arr
