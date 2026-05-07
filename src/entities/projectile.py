import pygame
import src.tileset as Tileset
from src.tileset import TileType, TILE_SIZE
from src.camera import Camera
from src.entities.entity import Entity, EntityType
from src.animator import Animator

class Projectile(Entity):
    SPEED = 3

    def __init__(self, x: int, y: int, facing_right: bool):
        super().__init__(x,y, EntityType.PROJECTILE)
        self.pos = [float(x), float(y)] 
        self.facing_right = facing_right
        self.collected = False 

        self.animator = Animator(
            frames=[TileType.ARROW.value],
            speed=8
        )

    def update(self, player_rect: pygame.Rect):
        if self.facing_right:
            self.pos[0] += self.SPEED
        else:
            self.pos[0] -= self.SPEED
        
        self.x = int(self.pos[0])
        self.y = int(self.pos[1])

        self.animator.update()

    def draw(self, surface: pygame.Surface, camera: Camera):
        if self.collected:
            return
        camera_pos = camera.get_pos()
        frame = self.animator.get_frame()

        if not self.facing_right:
            frame = pygame.transform.flip(frame, True, False)
        
        surface.blit(frame, (
            self.pos[0] - camera_pos[0],
            self.pos[1] - camera_pos[1]
        ))