import os
from PIL import Image, ImageDraw

def create_winter_arc_icon(ico_path):
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Dark squircle background
    pad = 16
    draw.rounded_rectangle(
        [(pad, pad), (size - pad, size - pad)],
        radius=54,
        fill=(15, 23, 42, 245),
        outline=(56, 189, 248, 180),
        width=3
    )

    # 2. Inner subtle glow ring
    inner_pad = pad + 6
    draw.rounded_rectangle(
        [(inner_pad, inner_pad), (size - inner_pad, size - inner_pad)],
        radius=48,
        outline=(56, 189, 248, 40),
        width=2
    )

    # 3. Draw a stylized Winter Arc Crescent / Flame emblem in center
    cx, cy = size // 2, size // 2

    # Draw cyan glow circle
    glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse([(cx - 65, cy - 65), (cx + 65, cy + 65)], fill=(10, 132, 255, 35))
    glow_draw.ellipse([(cx - 45, cy - 45), (cx + 45, cy + 45)], fill=(56, 189, 248, 55))
    img = Image.alpha_composite(img, glow)
    draw = ImageDraw.Draw(img)

    # Draw an elegant athletic Winter Arc Crescent Moon / Blade in neon cyan
    arc_points = [
        (cx, cy - 60),
        (cx + 42, cy - 30),
        (cx + 52, cy + 15),
        (cx + 30, cy + 55),
        (cx - 5, cy + 68),
        (cx + 15, cy + 40),
        (cx + 25, cy + 10),
        (cx + 12, cy - 25),
        (cx, cy - 60),
    ]
    draw.polygon(arc_points, fill=(56, 189, 248, 255))

    # Draw an inner core flame in radiant white/cyan
    core_points = [
        (cx - 10, cy - 35),
        (cx + 8, cy - 10),
        (cx + 12, cy + 25),
        (cx - 8, cy + 50),
        (cx - 28, cy + 20),
        (cx - 25, cy - 10),
        (cx - 10, cy - 35)
    ]
    draw.polygon(core_points, fill=(240, 249, 255, 230))

    # Inner flame cut
    draw.ellipse([(cx - 18, cy - 5), (cx + 2, cy + 25)], fill=(15, 23, 42, 255))

    # Save multi-size .ico
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    img.save(ico_path, format="ICO", sizes=sizes)
    print(f"Created icon at: {ico_path}")

if __name__ == "__main__":
    target = r"C:\Users\Admin\Documents\Winter Arc\app_icon.ico"
    create_winter_arc_icon(target)
