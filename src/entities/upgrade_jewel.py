import pygame
import math
import src.tileset as Tileset
from src.tileset import TileType, TILE_SIZE
from src.camera import Camera
from src.entities.entity import Entity, EntityType
from src.animator import Animator

class UpgradeJewel(Entity):
    BOB_SPEED = 0.08
    BOB_HEIGHT = 1
    PULSE_SPEED = 0.05

    BLUE = (0, 150, 255)

    def __init__(self, x: int, y: int):
        super().__init__(x, y, EntityType.UPGRADE_JEWEL)
        self.pos = [float(x), float(y)]
        self.spawn_y = float(y)
        self._bob_timer = 0.0
        self._pulse_timer = 0.0
        self.collected = False

        self.animator = Animator(
            frames=[TileType.JEWEL.value],
            speed= 10
        )

    def update(self, player_rect: pygame.Rect):
        # bob up and down
        self._bob_timer += self.BOB_SPEED
        self.pos[1] = self.spawn_y + math.sin(self._bob_timer) * self.BOB_HEIGHT
        self.y = int(self.pos[1])

        self._pulse_timer += self.PULSE_SPEED

        if self.rect.colliderect(player_rect):
            self.collected = True
        
        self.animator.update()
    
    def draw(self, surface: pygame.Surface, camera: Camera):
        if self.collected:
            return
        
        camera_pos = camera.get_pos()
        frame = self.animator.get_frame()

        #Blue tint
        frame = Tileset.change_letter_color(frame, self.BLUE)

        scale = int(8 + abs(math.sin(self._pulse_timer)) * 4)
        frame = pygame.transform.scale(frame, (scale, scale))

        # Center the scaled frame on its position
        draw_x = self.pos[0] - camera_pos[0] - (scale - TILE_SIZE) // 2
        draw_y = self.pos[1] - camera_pos[1] - (scale - TILE_SIZE) // 2

        surface.blit(frame, (draw_x, draw_y))
