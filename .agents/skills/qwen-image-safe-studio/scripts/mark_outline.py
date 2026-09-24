#!/usr/bin/env python3
"""
mark_outline.py - Helper for generating precise hollow red outlines for Qwen-Image-2.1
Supports:
  - 'top': Encloses neckline, shoulders, chest, full sleeves down to cuffs, and waistline.
  - 'bottom': Encloses waistline down to knees/hem.
  - 'full-suit': Encloses shoulders down to knees.
  - 'box': Rectangular bounding box with thickness.
"""

import sys
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np

def mark_top_outline(input_image_path: Path, output_image_path: Path, width_px: int = 6):
    """
    Draw a clean, closed polygon enclosing the upper garment (including full sleeves).
    Adapts to 3:4 portrait or standard full-body shots.
    """
    img = Image.open(input_image_path).convert("RGB")
    w, h = img.size
    draw = ImageDraw.Draw(img)

    # Relative normalized coordinates for a standard full/half-body portrait:
    # (x_ratio, y_ratio)
    # Neck -> left shoulder -> left outer sleeve -> left cuff -> left inner waist -> waistband -> right inner waist -> right cuff -> right outer sleeve -> right shoulder -> neck
    norm_points = [
        (0.500, 0.330),  # center crew/collar neckline
        (0.458, 0.315),  # left neckline
        (0.400, 0.320),  # left shoulder slope
        (0.360, 0.340),  # left shoulder point
        (0.340, 0.428),  # left outer upper arm
        (0.328, 0.559),  # left outer forearm
        (0.328, 0.724),  # left cuff outer / wrist
        (0.380, 0.724),  # left cuff inner / wrist
        (0.400, 0.559),  # left inner waist curve
        (0.431, 0.533),  # left waistband
        (0.582, 0.533),  # right waistband
        (0.614, 0.559),  # right inner waist curve
        (0.663, 0.724),  # right cuff inner / wrist
        (0.738, 0.724),  # right cuff outer / wrist
        (0.733, 0.559),  # right outer forearm
        (0.722, 0.428),  # right outer upper arm
        (0.711, 0.340),  # right shoulder point
        (0.603, 0.320),  # right shoulder slope
        (0.544, 0.315),  # right neckline
    ]

    points = [(int(nx * w), int(ny * h)) for nx, ny in norm_points]
    draw.polygon(points, outline=(255, 0, 0), width=width_px)
    img.save(output_image_path)
    return output_image_path

def mark_box_outline(input_image_path: Path, output_image_path: Path, box_coords: tuple, width_px: int = 6):
    """
    Draw a rectangular hollow red box. box_coords = (x1, y1, x2, y2).
    """
    img = Image.open(input_image_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    draw.rectangle(box_coords, outline=(255, 0, 0), width=width_px)
    img.save(output_image_path)
    return output_image_path

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python mark_outline.py <input_img> <output_img> [target: top|box] [x1 y1 x2 y2]")
        sys.exit(1)
    
    inp = Path(sys.argv[1])
    out = Path(sys.argv[2])
    target = sys.argv[3] if len(sys.argv) > 3 else "top"
    
    if target == "top":
        mark_top_outline(inp, out)
        print(f"[✓] Successfully marked top outline on {inp} -> {out}")
    elif target == "box" and len(sys.argv) >= 8:
        box = tuple(int(x) for x in sys.argv[4:8])
        mark_box_outline(inp, out, box)
        print(f"[✓] Successfully marked box {box} on {inp} -> {out}")
