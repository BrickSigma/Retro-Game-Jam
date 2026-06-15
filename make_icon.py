"""
Extracts the PLAYER_IDLE tile (index 76) from the tileset and saves it as icon.ico.
Run once whenever you want to regenerate the icon.
"""
from PIL import Image

TILE_SIZE = 8
PLAYER_IDLE_INDEX = 76
TILESET_COLS = 16

tile_x = (PLAYER_IDLE_INDEX % TILESET_COLS) * TILE_SIZE
tile_y = (PLAYER_IDLE_INDEX // TILESET_COLS) * TILE_SIZE

src = Image.open("assets/tileset.png").convert("RGBA")
tile = src.crop((tile_x, tile_y, tile_x + TILE_SIZE, tile_y + TILE_SIZE))

sizes = [16, 32, 48, 64, 128, 256]
frames = [tile.resize((s, s), Image.NEAREST) for s in sizes]

frames[0].save(
    "icon.ico",
    format="ICO",
    sizes=[(s, s) for s in sizes],
    append_images=frames[1:],
)

print("icon.ico created successfully.")
