import math
import sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import logging

# --- Constants ---
BLUR_R = 0.035
WIDTH = 1920
HEIGHT = 1080
CHILDREN_SIZE = 0.6
DIM = 0.6

SHADER_ALPHA = 0.5
SHADER_POWER = 0.035

logging.basicConfig(level=logging.DEBUG, format='[%(name)s][%(funcName)s] %(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Helper functions (unchanged) ---
def rotate_point(x, y, θ, r) -> tuple[float, float]:
    xo = r * math.cos(math.radians(θ))
    yo = r * math.sin(math.radians(θ))
    return x + xo, y + yo

def compute_intersection(
    x0: float, y0: float,
    x1: float, y1: float,
    x2: float, y2: float,
    x3: float, y3: float
):
    a1 = y1 - y0
    b1 = x0 - x1
    c1 = x1 * y0 - x0 * y1
    a2 = y3 - y2
    b2 = x2 - x3
    c2 = x3 * y2 - x2 * y3
    denominator = (a1 * b2 - a2 * b1)
    if abs(denominator) < 1e-9:
        return float('inf'), float('inf')
    return (b2 * c1 - b1 * c2) / denominator, (a1 * c2 - a2 * c1) / denominator

def getDPower(width: float, height: float, deg: float):
    l1 = 0, 0, width, 0
    l2 = 0, height, *rotate_point(0, height, deg, (width ** 2 + height ** 2) ** 0.5)
    return compute_intersection(*l1, *l2)[0] / width

# --- Main image generation function ---
def run_pillow(ipt: str, opt: str, song_title: str):
    """
    Generates the image and adds a song title inside the bottom-left of the central parallelogram.
    """
    # 1. Load and prepare the source image
    with Image.open(ipt) as im:
        im = im.convert("RGBA")
        r = im.width / im.height
        target_r = WIDTH / HEIGHT
        if r > target_r:
            new_width = int(im.height * target_r)
            left = (im.width - new_width) / 2
            im_cropped = im.crop((left, 0, left + new_width, im.height))
        else:
            new_height = int(im.width / target_r)
            top = (im.height - new_height) / 2
            im_cropped = im.crop((0, top, im.width, top + new_height))
    main_image = im_cropped.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)

    # 2. Create background and dimming layer
    background = main_image.filter(ImageFilter.GaussianBlur((WIDTH + HEIGHT) * BLUR_R))
    dim_alpha = int(255 * (1.0 - DIM))
    dim_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, dim_alpha))
    canvas = Image.alpha_composite(background, dim_layer)

    # 3. Calculate coordinates for the foreground element
    dpower = getDPower(WIDTH, HEIGHT, 75)
    child_w = WIDTH * CHILDREN_SIZE
    child_h = HEIGHT * CHILDREN_SIZE
    x0 = (WIDTH - child_w) / 2
    y0 = (HEIGHT - child_h) / 2
    x1 = x0 + child_w
    y1 = y0 + child_h
    skew = (x1 - x0) * dpower
    p_verts = [
        (x0 + skew, y0), (x1, y0),
        (x1 - skew, y1), (x0, y1),
    ]

    # 4. Create shadow and paste foreground image
    shadow_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)
    shadow_fill = (0, 0, 0, int(255 * SHADER_ALPHA))
    shadow_draw.polygon(p_verts, fill=shadow_fill)
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur((WIDTH + HEIGHT) * SHADER_POWER))
    canvas = Image.alpha_composite(canvas, shadow_layer)
    child_image_size = (int(child_w), int(child_h))
    child_image = main_image.resize(child_image_size, Image.Resampling.LANCZOS)
    mask = Image.new("L", child_image_size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_skew = child_w * dpower
    mask_verts = [
        (mask_skew, 0), (child_w, 0),
        (child_w - mask_skew, child_h), (0, child_h),
    ]
    mask_draw.polygon(mask_verts, fill=255)
    canvas.paste(child_image, (int(x0), int(y0)), mask)

    # 5. Draw the song title inside the parallelogram
    draw = ImageDraw.Draw(canvas)
    
    # Define text properties
    text_padding = 40  # Padding from the parallelogram edges
    shadow_offset = 3  # Pixel offset for the text shadow
    font_size = int(child_h * 0.08) # Font size relative to the central image height
    text_color = "white"
    shadow_color = "black"

    try:
        font = ImageFont.truetype("../font.ttf", size=font_size)
    except IOError:
        logger.warning("Custom font not found. Using default font.")
        try:
            # Pillow 10.0.0+ has a more robust default font
            font = ImageFont.load_default(size=font_size)
        except AttributeError:
            font = ImageFont.load_default()

    # The bottom-left vertex of the parallelogram is at (x0, y1)
    # We will position the text relative to this point.
    
    # Get the bounding box of the text to correctly calculate its height
    text_bbox = draw.textbbox((0, 0), song_title, font=font)
    text_height = text_bbox[3] - text_bbox[1]
    
    # Calculate the top-left coordinate for drawing the text
    text_x = x0 + text_padding
    text_y = y1 - text_padding - text_height
    
    # Draw the shadow first (black text, offset by a few pixels)
    draw.text(
        (text_x + shadow_offset, text_y + shadow_offset),
        song_title,
        font=font,
        fill=shadow_color
    )
    
    # Draw the main text on top of the shadow
    draw.text(
        (text_x, text_y),
        song_title,
        font=font,
        fill=text_color
    )

    # 6. Save the final result
    canvas.save(opt, "PNG")
    logger.info(f"Image with title '{song_title}' successfully saved to {opt}")


if __name__ == "__main__":
    input_path = r"D:\Phigros-DEV\simulation_and_rendering\PhiAutoRender-main\Unpack\illustration\雪降り雪が降っている.AiSSw夜輪ft結月ゆかり.png"
    output_path = "cover.png"
    title = "雪降り雪が降っている"

    run_pillow(input_path, output_path, title)