"""
Module to handle the tileset and grab individual tiles
"""
from enum import Enum, unique
import pygame

from src.constants import resource_path

TILE_SIZE = 8

tileset: None | pygame.Surface = None

_chars = [
    "a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z", 
    "/", "-", ":", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", " ", ".", "!"]

_unused_color = (254, 254, 254)
"""Unused color used for color mapping functions"""

@unique
class TileType(Enum):
    NONE = None
    ARROW = 39
    BOX = 40
    BREAKABLE_BRICK = 41
    BRICK = 42
    BRICK_SOLID = 43
    BUTTON = 44
    CAVE_CORNER_1 = 45
    CAVE_CORNER_2= 46
    CAVE_CORNER_3 = 47
    CAVE_DETAIL = 48
    CAVE_FLOOR = 49
    CAVE_WALL = 50
    CHAIN = 51
    CHEST = 52
    COIN = 53
    COINS_PILE = 54
    CRYSTALS = 55
    DIRT = 56
    DOOR = 57
    FIRE = 58
    GHOST = 59
    GRASS = 60
    HEART = 61
    JEWEL = 62
    KEY = 63
    KEY_BLOCK = 64
    LADDER = 65
    LAVA = 66
    MAGIC = 67
    OVERHEAD_ROPE = 68
    PILLAR_BASE = 69
    PILLAR_MIDDLE = 70
    PILLAR_TOP = 71
    PLATFORM = 72
    PLAYER_CLIMB_1 = 73
    PLAYER_CLIMB_2 = 74
    PLAYER_FALL = 75
    PLAYER_IDLE = 76
    PLAYER_ROPE_1 = 77
    PLAYER_ROPE_2 = 78
    PLAYER_ROPE_3 = 79
    PLAYER_RUN_1 = 80
    PLAYER_RUN_2 = 81
    PLAYER_RUN_3 = 82
    PLAYER_RUN_4 = 83
    ROCKS = 84
    SHROOM = 85
    SPIDER = 86
    SPIDER_LINE = 87
    SPIDER_WEB = 88
    SPIKE = 89
    SPRING = 90
    STALAGMITE = 91
    LEVER = 92
    SWORD = 93
    TORCH = 94
    VINE = 95
    WINDOW = 96
    WINDOW_TOP = 97
    PLAYER_SLIDING = 98
    PLAYER_DEAD = 99
    GUARDIAN_IDLE = 100
    TORCH_1 = 101
    TORCH_2 = 102
    TORCH_3 = 103
    TORCH_4 = 104
    TORCH_5 = 105
    TORCH_6 = 106
    PERIOD = 107
    EXCLAMATION = 108

def init():
    global tileset
    if tileset != None:
        return
    
    tileset = pygame.image.load(resource_path("assets/tileset.png"))
    tileset = tileset.convert_alpha()

def get_tile(index: int) -> pygame.Surface:
    if tileset == None:
        raise Exception("Tileset not initialized yet!")
    
    if index > 256:
        raise IndexError()
    
    x = index % 16
    y = (index // 16)
    return tileset.subsurface((x*TILE_SIZE, y*TILE_SIZE, TILE_SIZE, TILE_SIZE))

def render_tile(surf: pygame.Surface, tile: pygame.Surface, x: int, y: int, offset_x: int = 0, offset_y: int = 0) -> None:
    """Render a tile to an indexed point on the surface"""
    surf.blit(tile, (x*TILE_SIZE + offset_x, y*TILE_SIZE + offset_y))

def get_char(char: str) -> pygame.Surface:
    """Get the tile for a single character"""
    
    char = char.lower()
    if char not in _chars:
        raise Exception("Character not in characters list!")
    
    if char == " ":
        surface = pygame.Surface((8, 8), pygame.SRCALPHA)
        return surface
    
    if char == ".":
        surface = get_tile(TileType.PERIOD.value)
        return surface
    
    if char == "!":
        surface = get_tile(TileType.EXCLAMATION.value)
        return surface
    
    return get_tile(_chars.index(char))

def render_string(string: str) -> pygame.Surface:
    """
    Render a string as a set of tiles
    """
    length = len(string)
    string = string.lower()

    surface = pygame.Surface((length*TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    for i in range(0, length):
        if string[i] not in _chars:
            surface.blit(get_char(" "), (i*TILE_SIZE,0))
        else:
            surface.blit(get_char(string[i]), (i*TILE_SIZE,0))
    
    return surface

def swap_color(tile: pygame.Surface, old_color: tuple[int, int, int], new_color: tuple[int, int, int]) -> pygame.Surface:
    temp_surface = pygame.Surface(tile.size, pygame.SRCALPHA)
    temp_surface.fill(_unused_color)
    temp_surface.blit(tile)
    temp_surface.set_colorkey(old_color)

    surface = pygame.Surface(tile.size)
    surface.fill(new_color)
    surface.blit(temp_surface)
    surface.set_colorkey(_unused_color)
    return surface

def change_letter_color(tile: pygame.Surface, color: tuple[int, int, int]) -> pygame.Surface:
    """
    Convert the colors on a character tile (or even string).

    This essentially converts any white pixels to the new color.
    """
    return swap_color(tile, (255, 255, 255), color)

LIGHT_BLUE = (203, 219, 252)
GREY = (104, 111, 153)

class TextBox:
    def __init__(self, 
                 text: str, 
                 x: int, 
                 y: int, 
                 x_offset: int = 4, 
                 y_offset: int = 4,
                 color: tuple[int, int, int] = LIGHT_BLUE):
        self.surface = change_letter_color(render_string(text), color)
        self.x = x
        self.y = y
        self.x_offset = x_offset
        self.y_offset = y_offset

    def draw(self, dest: pygame.Surface):
        render_tile(dest, self.surface, self.x, self.y, self.x_offset, self.y_offset)

class GuideText:
    def __init__(self, text: str, pos: tuple[int, int]):
        self.text_surf = change_letter_color(render_string(text), LIGHT_BLUE)
        self.pos = list(pos)
