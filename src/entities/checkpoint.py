import pygame
import src.tileset as Tileset
from src.tileset import TileType, TILE_SIZE
from src.camera import Camera
from src.entities.entity import Entity, EntityType


class Checkpoint(Entity):
    COLOR_INACTIVE = (80,  80,  80)
    COLOR_ACTIVE   = (0, 200, 80)

    def __init__(self, x: int, y: int):
        super().__init__(x, y, EntityType.CHECKPOINT)
        self.activated = False
        self.collected = False  # never removed from entity list

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, TILE_SIZE, TILE_SIZE)

    def update(self, player_rect: pygame.Rect):
        pass

    def draw(self, surface: pygame.Surface, camera: Camera):
        camera_pos = camera.get_pos()
        frame = Tileset.get_tile(TileType.JEWEL.value)
        color = self.COLOR_ACTIVE if self.activated else self.COLOR_INACTIVE
        frame = Tileset.change_letter_color(frame, color)
        surface.blit(frame, (self.x - camera_pos[0], self.y - camera_pos[1]))
