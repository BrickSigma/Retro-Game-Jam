"""
Module to handle the tileset and grab individual tiles
"""
from enum import Enum, unique
import pygame

TILE_SIZE = 8

tileset: None | pygame.Surface = None

_chars = [
    "a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z", 
    "/", "-", ":", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", " "]

_unused_color = (254, 254, 254)
"""Unused color used for color mapping functions"""

@unique
class TileType(Enum):
    NONE = None
    ARROW = 39
    BRICK = 40
    BROKEN_BRICK = 41
    SOLID_BRICK = 42
    CAVE_TOP_LEFT = 43
    CAVE_TOP_RIGHT = 44
    CAVE_BOTTOM_LEFT = 45
    CAVE_BOTTOM_RIGHT = 46
    CAVE_DETAIL = 47
    CAVE_FLOOR = 48
    CAVE_ROOF = 49
    CAVE_WALL_LEFT = 50
    CAVE_WALL_RIGHT = 51
    RAMP_RIGHT = 52
    RAMP_LEFT = 53
    CAVE_CORNER_LEFT = 54
    CAVE_CORNER_RIGHT = 55
    PILLAR_TOP = 56
    PILLAR_BOTTOM = 57
    PILLAR_MIDDLE = 58
    LADDER = 59

def init():
    global tileset
    if tileset != None:
        return
    
    tileset = pygame.image.load("./assets/tileset.png")
    tileset = tileset.convert_alpha()

def get_tile(index: int) -> pygame.Surface:
    if tileset == None:
        raise Exception("Tileset not initialized yet!")
    
    if index > 256:
        raise IndexError()
    
    x = index % 16
    y = (index // 16)
    return tileset.subsurface((x*TILE_SIZE, y*TILE_SIZE, TILE_SIZE, TILE_SIZE))

def render_tile(surf: pygame.Surface, tile: pygame.Surface, x: int, y: int) -> None:
    """Render a tile to an indexed point on the surface"""
    surf.blit(tile, (x*TILE_SIZE, y*TILE_SIZE))

def get_char(char: str) -> pygame.Surface:
    """Get the tile for a single character"""
    
    char = char.lower()
    if char not in _chars:
        raise Exception("Character not in characters list!")
    
    if char == " ":
        surface = pygame.Surface((8, 8), pygame.SRCALPHA)
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

    This essentially converts any black pixels to the new color.
    """
    return swap_color(tile, (255, 255, 255), color)
