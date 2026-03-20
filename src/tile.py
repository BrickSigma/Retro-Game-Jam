from enum import Enum, unique
from src.tileset import TILE_SIZE, TileType
import src.tileset as TileSet
import pygame

@unique
class TileFlip(Enum):
    NONE = 0
    VERTICAL = 2
    HORIZONTAL = 4
    BOTH = 8

class Tile:
    def __init__(self, x: int, y: int, type: TileType, flip: TileFlip):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.type = type
        self.flip_x = False
        self.flip_y = False

        match flip:
            case TileFlip.HORIZONTAL:
                self.flip_x = True
            case TileFlip.VERTICAL:
                self.flip_y = True
            case TileFlip.BOTH:
                self.flip_x = True
                self.flip_y = True

    def draw(self, surface: pygame.Surface, pos: tuple[int]):
        surface.blit(pygame.transform.flip(TileSet.get_tile(self.type.value)), pos)
