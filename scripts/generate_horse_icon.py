from PIL import Image, ImageDraw
import os

def generate_horse_icon(path):
    size = 256
    img = Image.new('RGBA', (size, size), (0,0,0,0))
    draw = ImageDraw.Draw(img)

    # Draw a simple stylized horse silhouette: body ellipse, head rectangle, neck, legs, tail
    # Body
    body_bbox = (48, 80, 208, 168)
    draw.ellipse(body_bbox, fill=(30,30,30,255))

    # Neck and head
    draw.rectangle((168,48,198,88), fill=(30,30,30,255))
    draw.rectangle((190,32,220,68), fill=(30,30,30,255))

    # Legs
    draw.rectangle((72,160,88,232), fill=(30,30,30,255))
    draw.rectangle((112,160,130,232), fill=(30,30,30,255))
    draw.rectangle((152,160,170,232), fill=(30,30,30,255))
    draw.rectangle((192,160,210,232), fill=(30,30,30,255))

    # Tail
    draw.polygon([(48,112),(28,120),(48,136)], fill=(30,30,30,255))

    # Eye (white dot)
    draw.ellipse((204,44,210,50), fill=(255,255,255,255))

    # Save PNG and ICO
    os.makedirs(os.path.dirname(path), exist_ok=True)
    png_path = path.replace('.ico', '.png')
    img.save(png_path, format='PNG')
    # Save ICO (Pillow supports ICO writing)
    img.save(path, format='ICO', sizes=[(256,256),(64,64),(32,32),(16,16)])

if __name__ == '__main__':
    out_dir = os.path.join(os.path.dirname(__file__), '..', 'assets')
    os.makedirs(out_dir, exist_ok=True)
    ico_path = os.path.join(out_dir, 'horse.ico')
    generate_horse_icon(ico_path)
    print('Generated', ico_path)
