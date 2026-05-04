import pygame
import src.tileset as Tileset
from src.tileset import TILE_SIZE
from src.camera import Camera
from src.entities.entity import Entity, EntityType

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

    def draw(self, surface: pygame.Surface, camera: Camera):
        camera_pos = camera.get_pos()
        frame = Tileset.get_tile(self.type.get_tile_type().value)
        frame = pygame.transform.rotate(frame, -self.rotation)
        surface.blit(frame, (self._pos[0] - camera_pos[0], self._pos[1] - camera_pos[1]))