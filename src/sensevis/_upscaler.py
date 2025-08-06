import csv
import random
from pathlib import Path
from typing import List, Tuple, Set
import re

from PIL import Image

# Configuration
import os
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE_IMAGE_PATH = Path(os.path.join(root_dir, '8x10.png'))  # Base 10x8 background image
CSV_PATH = Path('centroid.csv')     # CSV with centroid data
OUTPUT_DIR = Path('bounding_box_gen')
OUTPUT_DIR.mkdir(exist_ok=True)

# Pixel grid dimensions (width x height)
GRID_W, GRID_H = 10, 8  # 10 columns, 8 rows
COORD_MAX = 100  # Coordinates range from 1..100 inclusive

BRIGHT_COLOR = (255, 248, 0)  # Bright yellow core (#fff800)
# Greenish fade palette for first ring (original)
FADED_COLORS_HEX = [
    '#8dff4d', '#35ebae', '#ccff66', '#99ff99', '#66ffcc'
]


def hex_to_rgb(hex_str: str):
    """Convert hex color like '#aabbcc' to RGB tuple."""
    hex_str = hex_str.lstrip('#')
    return (
        int(hex_str[0:2], 16),
        int(hex_str[2:4], 16),
        int(hex_str[4:6], 16),
    )  # type: ignore[return-value]


FADED_COLORS = [hex_to_rgb(h) for h in FADED_COLORS_HEX]  # type: ignore[var-annotated]

# Bright blue for halo (#08d5eb)
LAYER2_COLOR = (0x08, 0xD5, 0xEB)  # type: ignore[var-annotated]

# Blend weights (how much of the overlay color to apply)
LAYER1_BLEND = 0.6   # 60% faded color, 40% background (brighter first ring)
LAYER2_BLEND = 0.5   # 50% overlay, 50% background (brighter second ring)
LAYER3_BLEND = 0.25  # 25% overlay for third ring
LAYER4_BLEND = 0.1   # 10% overlay for fourth ring

# Corner pixels (diagonals) within a ring should be more transparent to smooth blending
CORNER_FACTOR = 0.85  # Multiplier (<1) applied to the base blend for corner pixels


def blend(color, base, alpha):
    """Blend two RGB colors using alpha (0‒1 for `color` contribution)."""
    return tuple(int(round(alpha * c + (1 - alpha) * b)) for c, b in zip(color, base))


def parse_positions(pos_str: str) -> List[float]:
    """Convert comma-separated positions (optionally wrapped in braces/brackets) to float list."""
    # Remove curly braces or square brackets if present
    cleaned = re.sub(r'[\{\}\[\]]', '', pos_str)
    vals: List[float] = []
    for token in cleaned.split(','):
        token = token.strip()
        if not token:
            continue
        try:
            vals.append(float(token))
        except ValueError:
            # Skip tokens that cannot be converted to float
            continue
    return vals


def coord_to_pixel(x: float, y: float) -> Tuple[int, int]:
    """Map (x, y) in 1‒100 range to zero-based pixel indices on GRID_W × GRID_H grid."""
    # Clamp to [1, 100]
    x = max(1.0, min(COORD_MAX, x))
    y = max(1.0, min(COORD_MAX, y))

    # Convert to 0-based range (0 <= sx < GRID_W, 0 <= sy < GRID_H)
    sx = (x - 1) / COORD_MAX * GRID_W  # float
    sy = (y - 1) / COORD_MAX * GRID_H

    px = int(min(GRID_W - 1, sx))
    py = int(min(GRID_H - 1, sy))
    return px, py


# Helper removed; using ring functions only


def get_ring(px: int, py: int, radius: int) -> List[Tuple[int, int]]:
    """Return pixel coordinates exactly `radius` Chebyshev distance from (px, py)."""
    ring = []
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            if dx == 0 and dy == 0:
                continue
            if max(abs(dx), abs(dy)) != radius:
                continue
            nx, ny = px + dx, py + dy
            if 0 <= nx < GRID_W and 0 <= ny < GRID_H:
                ring.append((nx, ny))
    return ring


def main():
    if not BASE_IMAGE_PATH.exists():
        raise FileNotFoundError(f'Base image {BASE_IMAGE_PATH} not found.')
    if not CSV_PATH.exists():
        raise FileNotFoundError(f'CSV file {CSV_PATH} not found.')

    base_img = Image.open(BASE_IMAGE_PATH).convert('RGB')
    if base_img.size != (GRID_W, GRID_H):
        # Optionally resize background to expected grid; assume nearest neighbor to keep pixel art
        base_img = base_img.resize((GRID_W, GRID_H), Image.Resampling.NEAREST)

    # Read centroid data
    with CSV_PATH.open(newline='') as csvfile:
        reader = csv.reader(csvfile)
        for idx, row in enumerate(reader):
            if not row or len(row) < 3:
                continue  # Skip malformed rows
            num_people = int(row[0])
            xs = parse_positions(row[1])
            ys = parse_positions(row[2])

            # Safety check
            if len(xs) != num_people or len(ys) != num_people:
                print(f'Row {idx}: person count mismatch, skipping.')
                continue

            img = base_img.copy()
            pixels = img.load()
            if pixels is None:
                raise RuntimeError('Failed to load image pixels.')

            # Draw each person
            cx, cy = (GRID_W - 1) / 2, (GRID_H - 1) / 2
            max_dist = ((cx)**2 + (cy)**2) ** 0.5
            for x, y in zip(xs, ys):
                # --- Bright pixel distributed across up to 4 pixels ---
                sx = (x - 1) / COORD_MAX * GRID_W
                sy = (y - 1) / COORD_MAX * GRID_H

                px0, py0 = int(min(GRID_W - 1, sx)), int(min(GRID_H - 1, sy))
                px1 = min(px0 + 1, GRID_W - 1)
                py1 = min(py0 + 1, GRID_H - 1)

                dx = sx - px0
                dy = sy - py0

                # Calculate distance to center for color blending
                dist = ((sx - cx) ** 2 + (sy - cy) ** 2) ** 0.5
                norm = min(dist / max_dist, 1.0)
                # Blend between a base color (dull yellow) and bright yellow
                BASE_YELLOW = (200, 180, 40)
                person_color = blend(BRIGHT_COLOR, BASE_YELLOW, 1 - norm)

                coords_weights = [
                    ((px0, py0), (1 - dx) * (1 - dy)),
                    ((px1, py0), dx * (1 - dy)),
                    ((px0, py1), (1 - dx) * dy),
                    ((px1, py1), dx * dy),
                ]

                bright_pixels: Set[Tuple[int, int]] = set()

                # Apply color with weight blending (strong weights use full color)
                for (bx, by), w in coords_weights:
                    if w < 0.1:
                        continue
                    pixels[bx, by] = person_color  # always set to person_color for visible weights
                    bright_pixels.add((bx, by))

                # --- Halo generation around bright pixels ---
                ring1_set: Set[Tuple[int, int]] = set()

                for bp in bright_pixels:
                    ring1 = get_ring(*bp, radius=1)
                    ring1_set.update(ring1)

                # First faded layer
                for nx, ny in ring1_set:
                    if (nx, ny) in bright_pixels:
                        continue
                    if pixels is not None:
                        base_col = pixels[nx, ny]
                        is_corner = any(abs(nx - bx) == 1 and abs(ny - by) == 1 for bx, by in bright_pixels)
                        blend_alpha = LAYER1_BLEND * CORNER_FACTOR if is_corner else LAYER1_BLEND
                        faded_raw = random.choice(FADED_COLORS)
                        new_col = blend(faded_raw, base_col, blend_alpha)
                        pixels[nx, ny] = new_col

                # Second faded layer (radius 2)
                ring2_set: Set[Tuple[int, int]] = set()
                for bp in bright_pixels:
                    ring2_set.update(get_ring(*bp, radius=2))

                for nx, ny in ring2_set:
                    if (nx, ny) in bright_pixels or (nx, ny) in ring1_set:
                        continue
                    if pixels is not None:
                        base_col = pixels[nx, ny]
                        is_corner = any(abs(nx - bp[0]) == 2 and abs(ny - bp[1]) == 2 for bp in bright_pixels)
                        blend_alpha = LAYER2_BLEND * CORNER_FACTOR if is_corner else LAYER2_BLEND
                        new_col = blend(LAYER2_COLOR, base_col, blend_alpha)
                        pixels[nx, ny] = new_col

                # Third faded layer (radius 3)
                ring3_set: Set[Tuple[int, int]] = set()
                for bp in bright_pixels:
                    ring3_set.update(get_ring(*bp, radius=3))

                for nx, ny in ring3_set:
                    if (nx, ny) in bright_pixels or (nx, ny) in ring1_set or (nx, ny) in ring2_set:
                        continue
                    if pixels is not None:
                        base_col = pixels[nx, ny]
                        is_corner = any(abs(nx - bp[0]) == 3 and abs(ny - bp[1]) == 3 for bp in bright_pixels)
                        blend_alpha = LAYER3_BLEND * CORNER_FACTOR if is_corner else LAYER3_BLEND
                        new_col = blend(LAYER2_COLOR, base_col, blend_alpha)
                        pixels[nx, ny] = new_col

                # Fourth faded layer (radius 4)
                ring4_set: Set[Tuple[int, int]] = set()
                for bp in bright_pixels:
                    ring4_set.update(get_ring(*bp, radius=4))

                for nx, ny in ring4_set:
                    if (nx, ny) in bright_pixels or (nx, ny) in ring1_set or (nx, ny) in ring2_set or (nx, ny) in ring3_set:
                        continue
                    if pixels is not None:
                        base_col = pixels[nx, ny]
                        is_corner = any(abs(nx - bp[0]) == 4 and abs(ny - bp[1]) == 4 for bp in bright_pixels)
                        blend_alpha = LAYER4_BLEND * CORNER_FACTOR if is_corner else LAYER4_BLEND
                        new_col = blend(LAYER2_COLOR, base_col, blend_alpha)
                        pixels[nx, ny] = new_col

            name = idx + 1
            name1 = idx + 100

            # Save image
            out_path = OUTPUT_DIR / f'{name1}.png'
            img.save(out_path)
            print(f'Saved {out_path}')

            # --- Custom upscale to 640x480 ---
            UPSCALED_W, UPSCALED_H = 640, 480
            BLOCK_W, BLOCK_H = 64, 60  # Each 10x8 pixel becomes a 64x60 block
            upscaled = Image.new('RGB', (UPSCALED_W, UPSCALED_H), (0, 0, 0))
            src_pixels = img.load()
            up_pixels = upscaled.load()
            if src_pixels is None or up_pixels is None:
                raise RuntimeError('Failed to load upscaled image pixels.')
            for gy in range(GRID_H):
                for gx in range(GRID_W):
                    color = src_pixels[gx, gy]
                    for dy in range(BLOCK_H):
                        for dx in range(BLOCK_W):
                            ux = gx * BLOCK_W + dx
                            uy = gy * BLOCK_H + dy
                            up_pixels[ux, uy] = color
            out_upscaled = OUTPUT_DIR / f'{name}.png'
            upscaled.save(out_upscaled)
            print(f'Saved upscaled {out_upscaled}')

    print(f'All images saved to {OUTPUT_DIR.resolve()}')

def generate_image_from_centroids(centroids: List[Tuple[float, float]], userInput):
    """
    Generate a pixelized image from a list of (x, y) centroids (x in [1,32], y in [1,24]),
    using 8x10.png as the base, and save as bounding_box_gen/live.png.
    If no centroids are given or all centroids are (0,0), generates a blank image.
    """
    # Check if centroids is empty or contains only (0,0) coordinates
    if not centroids or all(x == 0 and y == 0 for x, y in centroids):
        print("No valid centroids detected, generating blank image...")
        generate_blank(userInput)
        # Still create the live.png file as a blank image
        if not BASE_IMAGE_PATH.exists():
            raise FileNotFoundError(f'Base image {BASE_IMAGE_PATH} not found.')
        base_img = Image.open(BASE_IMAGE_PATH).convert('RGB')
        if base_img.size != (GRID_W, GRID_H):
            base_img = base_img.resize((GRID_W, GRID_H), Image.Resampling.NEAREST)
        out_path = OUTPUT_DIR / 'live.png'
        base_img.save(out_path)
        print(f'Saved blank {out_path}')
        return
    
    if not BASE_IMAGE_PATH.exists():
        raise FileNotFoundError(f'Base image {BASE_IMAGE_PATH} not found.')

    base_img = Image.open(BASE_IMAGE_PATH).convert('RGB')
    if base_img.size != (GRID_W, GRID_H):
        base_img = base_img.resize((GRID_W, GRID_H), Image.Resampling.NEAREST)

    img = base_img.copy()
    pixels = img.load()
    if pixels is None:
        raise RuntimeError('Failed to load image pixels.')

    # Map input range [1,32]x[1,24] to [0,9]x[0,7]
    def map_coord(x, y):
        sx = (x - 1) / 31 * (GRID_W - 1)  # 0..9
        sy = (y - 1) / 23 * (GRID_H - 1)  # 0..7
        return sx, sy

    cx, cy = (GRID_W - 1) / 2, (GRID_H - 1) / 2
    max_dist = ((cx)**2 + (cy)**2) ** 0.5

    bright_pixels: Set[Tuple[int, int]] = set()
    for x, y in centroids:
        sx, sy = map_coord(x, y)
        px0, py0 = int(min(GRID_W - 1, sx)), int(min(GRID_H - 1, sy))
        px1 = min(px0 + 1, GRID_W - 1)
        py1 = min(py0 + 1, GRID_H - 1)
        dx = sx - px0
        dy = sy - py0
        dist = ((sx - cx) ** 2 + (sy - cy) ** 2) ** 0.5
        norm = min(dist / max_dist, 1.0)
        BASE_YELLOW = (200, 180, 40)
        person_color = blend(BRIGHT_COLOR, BASE_YELLOW, 1 - norm)
        coords_weights = [
            ((px0, py0), (1 - dx) * (1 - dy)),
            ((px1, py0), dx * (1 - dy)),
            ((px0, py1), (1 - dx) * dy),
            ((px1, py1), dx * dy),
        ]
        for (bx, by), w in coords_weights:
            if w < 0.1:
                continue
            pixels[bx, by] = person_color
            bright_pixels.add((bx, by))

    # Halo layers
    ring1_set: Set[Tuple[int, int]] = set()
    for bp in bright_pixels:
        ring1_set.update(get_ring(*bp, radius=1))
    for nx, ny in ring1_set:
        if (nx, ny) in bright_pixels:
            continue
        base_col = pixels[nx, ny]
        is_corner = any(abs(nx - bx) == 1 and abs(ny - by) == 1 for bx, by in bright_pixels)
        blend_alpha = LAYER1_BLEND * CORNER_FACTOR if is_corner else LAYER1_BLEND
        faded_raw = random.choice(FADED_COLORS)
        new_col = blend(faded_raw, base_col, blend_alpha)
        pixels[nx, ny] = new_col
    ring2_set: Set[Tuple[int, int]] = set()
    for bp in bright_pixels:
        ring2_set.update(get_ring(*bp, radius=2))
    for nx, ny in ring2_set:
        if (nx, ny) in bright_pixels or (nx, ny) in ring1_set:
            continue
        base_col = pixels[nx, ny]
        is_corner = any(abs(nx - bp[0]) == 2 and abs(ny - bp[1]) == 2 for bp in bright_pixels)
        blend_alpha = LAYER2_BLEND * CORNER_FACTOR if is_corner else LAYER2_BLEND
        new_col = blend(LAYER2_COLOR, base_col, blend_alpha)
        pixels[nx, ny] = new_col
    ring3_set: Set[Tuple[int, int]] = set()
    for bp in bright_pixels:
        ring3_set.update(get_ring(*bp, radius=3))
    for nx, ny in ring3_set:
        if (nx, ny) in bright_pixels or (nx, ny) in ring1_set or (nx, ny) in ring2_set:
            continue
        base_col = pixels[nx, ny]
        is_corner = any(abs(nx - bp[0]) == 3 and abs(ny - bp[1]) == 3 for bp in bright_pixels)
        blend_alpha = LAYER3_BLEND * CORNER_FACTOR if is_corner else LAYER3_BLEND
        new_col = blend(LAYER2_COLOR, base_col, blend_alpha)
        pixels[nx, ny] = new_col
    ring4_set: Set[Tuple[int, int]] = set()
    for bp in bright_pixels:
        ring4_set.update(get_ring(*bp, radius=4))
    for nx, ny in ring4_set:
        if (nx, ny) in bright_pixels or (nx, ny) in ring1_set or (nx, ny) in ring2_set or (nx, ny) in ring3_set:
            continue
        base_col = pixels[nx, ny]
        is_corner = any(abs(nx - bp[0]) == 4 and abs(ny - bp[1]) == 4 for bp in bright_pixels)
        blend_alpha = LAYER4_BLEND * CORNER_FACTOR if is_corner else LAYER4_BLEND
        new_col = blend(LAYER2_COLOR, base_col, blend_alpha)
        pixels[nx, ny] = new_col

    # Save image
    out_path = OUTPUT_DIR / 'ignore.png'
    img.save(out_path)
    print(f'Saved {out_path}')

    # --- Custom upscale to 640x480 ---
    UPSCALED_W, UPSCALED_H = 640, 480
    BLOCK_W, BLOCK_H = 64, 60  # Each 10x8 pixel becomes a 64x60 block
    upscaled = Image.new('RGB', (UPSCALED_W, UPSCALED_H), (0, 0, 0))
    src_pixels = img.load()
    up_pixels = upscaled.load()
    if src_pixels is None or up_pixels is None:
        raise RuntimeError('Failed to load upscaled image pixels.')
    for gy in range(GRID_H):
        for gx in range(GRID_W):
            color = src_pixels[gx, gy]
            for dy in range(BLOCK_H):
                for dx in range(BLOCK_W):
                    ux = gx * BLOCK_W + dx
                    uy = gy * BLOCK_H + dy
                    up_pixels[ux, uy] = color
    out_upscaled = OUTPUT_DIR / f'{userInput}.png'
    upscaled.save(out_upscaled)
    #print(f'Saved upscaled {out_upscaled}')

def generate_blank(userInput):
    base_img = Image.open(BASE_IMAGE_PATH).convert('RGB')
    if base_img.size != (GRID_W, GRID_H):
        base_img = base_img.resize((GRID_W, GRID_H), Image.Resampling.NEAREST)

    img = base_img.copy()

    UPSCALED_W, UPSCALED_H = 640, 480
    BLOCK_W, BLOCK_H = 64, 60  # Each 10x8 pixel becomes a 64x60 block
    upscaled = Image.new('RGB', (UPSCALED_W, UPSCALED_H), (0, 0, 0))
    src_pixels = img.load()
    up_pixels = upscaled.load()
    if src_pixels is None or up_pixels is None:
        raise RuntimeError('Failed to load upscaled image pixels.')
    for gy in range(GRID_H):
        for gx in range(GRID_W):
            color = src_pixels[gx, gy]
            for dy in range(BLOCK_H):
                for dx in range(BLOCK_W):
                    ux = gx * BLOCK_W + dx
                    uy = gy * BLOCK_H + dy
                    up_pixels[ux, uy] = color
    out_upscaled = OUTPUT_DIR / f'{userInput}.png'
    upscaled.save(out_upscaled)
    #print(f'Saved blank {out_upscaled}')

if __name__ == '__main__':
    main() 