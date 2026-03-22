import pygame
import src.tileset as Tileset
from src.tileset import TILE_SIZE, TileType
from enum import Enum, auto
from src.camera import Camera

class EntityType(Enum):
    PLAYER = auto()
    SPIKE = auto()
    GATE = auto()
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

class Spike(Entity):
    def __init__(self, x, y, type, rotation: int):
        super().__init__(x, y, type)
        self.rotation = rotation
        self._pos = [x, y]

    @property
    def rect(self):
        if self.rotation == 0:
            return pygame.Rect(self.x, self.y + 4, TILE_SIZE, 3)
        elif self.rotation == -90:
            return pygame.Rect(self.x + 4, self.y, 3, TILE_SIZE)
        elif self.rotation == 90:
            return pygame.Rect(self.x, self.y, 3, TILE_SIZE)
        else:
            return pygame.Rect(self.x, self.y + 4, TILE_SIZE, 3)        

    def draw(self, surface, camera):
        camera_pos = camera.get_pos()
        frame = Tileset.get_tile(self.type.get_tile_type().value)
        frame = pygame.transform.rotate(frame, -self.rotation)
        surface.blit(frame, (self._pos[0] - camera_pos[0], self._pos[1] - camera_pos[1]))