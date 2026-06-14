"""
Animated torch entity
"""

import pygame

from src.animator import Animator
from src.camera import Camera
from src.entities.entity import Entity, EntityType
import src.tileset as Tileset
from src.tileset import TILE_SIZE, TileType

class Torch(Entity):
    def __init__(self, x: int, y: int):
        super().__init__(x, y, EntityType.TORCH)
        self.frames = Animator([
            TileType.TORCH_1.value,
            TileType.TORCH_2.value,
            TileType.TORCH_3.value,
            TileType.TORCH_4.value,
            TileType.TORCH_5.value,
            TileType.TORCH_6.value
        ], speed=8)

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, TILE_SIZE, TILE_SIZE)
    
    def draw(self, surface: pygame.Surface, camera: Camera):
        self.frames.update()
        frame = self.frames.get_frame()
        camera_pos = camera.get_pos()
        surface.blit(frame, (self.rect.x - camera_pos[0], self.rect.y - camera_pos[1]))
        
    def update(self, player_rect: pygame.Rect):
        pass