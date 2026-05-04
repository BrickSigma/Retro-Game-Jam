import pygame
import src.tileset as Tileset
from src.tileset import TILE_SIZE, TileType
from enum import Enum, auto
from src.camera import Camera

class EntityType(Enum):
    PLAYER = auto()
    SPIKE = auto()
    GATE = auto()
    GHOST = auto()
    UNKNOWN = auto()

    @staticmethod
    def from_name(name: str) -> EntityType:
        match name:
            case "player":
                return EntityType.PLAYER
            case "spike":
                return EntityType.SPIKE
            case "gate":
                return EntityType.GATE
            case "ghost":
                return EntityType.GHOST
            case _:
                return EntityType.UNKNOWN
            
    def get_tile_type(self) -> TileType:
        match self:
            case EntityType.PLAYER:
                return TileType.PLAYER_IDLE
            case EntityType.SPIKE:
                return TileType.SPIKE
            case EntityType.GATE:
                return TileType.DOOR
            case EntityType.GHOST:
                return EntityType.GHOST
            case _:
                return TileType.BOX

class Entity:
    def __init__(self, x: int, y: int, type: EntityType):
        self.x = x
        self.y = y
        self.type: EntityType = type

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, TILE_SIZE, TILE_SIZE)
    
    def draw(self, surface: pygame.Surface, camera: Camera):
        camera_pos = camera.get_pos()
        frame = Tileset.get_tile(self.type.get_tile_type().value)
        surface.blit(frame, (self.rect.x - camera_pos[0], self.rect.y - camera_pos[1]))
    def update(self, player_rect: pygame.Rect):
        pass