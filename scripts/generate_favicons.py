from PIL import Image
import cairosvg
import io
import os
from typing import Optional

def generate_favicons():
    """Generate favicon files in various formats from SVG source"""
    # Create static/images directory if it doesn't exist
    output_dir = 'static/images'
    os.makedirs(output_dir, exist_ok=True)
    
    # Read SVG file
    svg_path = 'static/images/qa-shield-logo.svg'
    try:
        with open(svg_path, 'rb') as svg_file:
            svg_data = svg_file.read()
    except FileNotFoundError:
        print(f"Error: Source SVG file not found: {svg_path}")
        return
    
    # Generate different sizes
    sizes = [(16, '16x16'), (32, '32x32'), (180, 'apple-touch-icon')]
    
    # Store 32x32 PNG for ICO conversion
    ico_image: Optional[Image.Image] = None
    
    for size, name in sizes:
        try:
            # Convert SVG to PNG with explicit type checking
            png_data = cairosvg.svg2png(
                bytestring=svg_data,
                output_width=size,
                output_height=size
            )
            
            if png_data is None:
                print(f"Error: Failed to generate PNG for size {size}x{size}")
                continue
                
            # Save as PNG
            output_path = os.path.join(output_dir, 
                f'favicon-{name}.png' if name != 'apple-touch-icon' else f'{name}.png')
            
            with open(output_path, 'wb') as png_file:
                png_file.write(png_data)
                
            print(f"Generated {output_path}")
            
            # Store 32x32 image for ICO
            if size == 32:
                ico_image = Image.open(io.BytesIO(png_data))
                
        except Exception as e:
            print(f"Error generating favicon for size {size}x{size}: {str(e)}")
    
    # Generate ICO file
    if ico_image:
        try:
            ico_path = os.path.join(output_dir, 'favicon.ico')
            ico_image.save(ico_path, format='ICO')
            print(f"Generated {ico_path}")
        except Exception as e:
            print(f"Error generating ICO file: {str(e)}")

if __name__ == '__main__':
    generate_favicons()
