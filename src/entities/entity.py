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
    JEWEL = auto()
    PROJECTILE = auto()
    UPGRADE_JEWEL = auto()
    SPIDER = auto()
    SPIDER_WEB = auto()
    WEB_ZONE = auto()
    BOSS = auto()
    BOSS_PROJECTILE = auto()
    CHECKPOINT = auto()
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
            case "jewel":
                return EntityType.JEWEL
            case "upgrade_jewel":
                return EntityType.UPGRADE_JEWEL
            case "spider":
                return EntityType.SPIDER
            case "boss":
                return EntityType.BOSS
            case "checkpoint":
                return EntityType.CHECKPOINT
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
                return TileType.GHOST
            case EntityType.JEWEL:
                return TileType.JEWEL
            case EntityType.PROJECTILE:
                return TileType.MAGIC
            case EntityType.UPGRADE_JEWEL:
                return TileType.JEWEL
            case EntityType.SPIDER:
                return TileType.SPIDER
            case EntityType.SPIDER_WEB:
                return TileType.SPIDER_LINE
            case EntityType.WEB_ZONE:
                return TileType.SPIDER_WEB
            case EntityType.BOSS:
                return TileType.GUARDIAN_IDLE
            case EntityType.BOSS_PROJECTILE:
                return TileType.MAGIC
            case EntityType.CHECKPOINT:
                return TileType.JEWEL
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