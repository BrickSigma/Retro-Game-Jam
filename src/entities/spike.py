import pygame
import src.tileset as Tileset
from src.tileset import TILE_SIZE
from src.camera import Camera
from src.entities.entity import Entity, EntityType

class Spike(Entity):
    def __init__(self, x, y, type, rotation: int):
        # pytmx gives the pre-rotation pivot (bottom-left of the unrotated tile,
        # with y already corrected by -tile_height). For rotated objects the visual
        # shifts away from that pivot, so we compensate here:
        #   rotation=90  (CW, tips right): visual extends DOWN from pivot → y += 8
        #   rotation=-90 (CCW, tips left): visual extends LEFT from pivot → x -= 8
        if rotation == 90:
            y += TILE_SIZE
        elif rotation == -90:
            x -= TILE_SIZE
        super().__init__(x, y, type)
        self.rotation = rotation
        self._pos = [x, y]

    @property
    def rect(self):
        if self.rotation == 0:
            return pygame.Rect(self.x + 2, self.y + 5, TILE_SIZE - 4, 3)
        elif self.rotation == 90:   # tips face left — hitbox on left edge
            return pygame.Rect(self.x, self.y + 2, 3, TILE_SIZE - 4)
        elif self.rotation == -90:    # tips face right — hitbox on right edge
            return pygame.Rect(self.x + 5, self.y + 2, 3, TILE_SIZE - 4)
        else:
            return pygame.Rect(self.x, self.y + 4, TILE_SIZE, 3)

    def draw(self, surface: pygame.Surface, camera: Camera):
        camera_pos = camera.get_pos()
        frame = Tileset.get_tile(self.type.get_tile_type().value)
        frame = pygame.transform.rotate(frame, -self.rotation)
        surface.blit(frame, (self._pos[0] - camera_pos[0], self._pos[1] - camera_pos[1]))

        # rect = self.rect
        # pygame.draw.rect(surface, (255, 0, 0), (rect.x - camera_pos[0], rect.y - camera_pos[1], rect.w, rect.h))
