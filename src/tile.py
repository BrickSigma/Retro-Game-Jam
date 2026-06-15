from enum import Enum, unique
from src.tileset import TILE_SIZE, TileType
import src.tileset as TileSet
import pygame

class Tile:
    def __init__(self, x: int, y: int, type: TileType, flip_x: bool, flip_y: bool):
        self.rect = pygame.Rect(x*TILE_SIZE, y*TILE_SIZE, TILE_SIZE, TILE_SIZE)
        self.type = type
        self.flip_x = flip_x
        self.flip_y = flip_y

    def draw(self, surface: pygame.Surface, pos: tuple[int]):
        surface.blit(pygame.transform.flip(TileSet.get_tile(self.type.value)), pos)
