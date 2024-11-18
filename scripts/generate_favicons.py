from PIL import Image
import cairosvg
import io
import os

def generate_favicons():
    # Create scripts/output directory if it doesn't exist
    output_dir = 'static/images'
    os.makedirs(output_dir, exist_ok=True)
    
    # Read SVG file
    with open('static/images/favicon.svg', 'rb') as svg_file:
        svg_data = svg_file.read()
    
    # Generate different sizes
    sizes = [(16, '16x16'), (32, '32x32'), (180, 'apple-touch-icon')]
    
    for size, name in sizes:
        # Convert SVG to PNG
        png_data = cairosvg.svg2png(
            bytestring=svg_data,
            output_width=size,
            output_height=size
        )
        
        # Save the PNG file
        output_path = os.path.join(output_dir, 
            f'favicon-{name}.png' if name != 'apple-touch-icon' else f'{name}.png')
        
        with open(output_path, 'wb') as png_file:
            png_file.write(png_data)
        
        print(f"Generated {output_path}")

if __name__ == '__main__':
    generate_favicons()
