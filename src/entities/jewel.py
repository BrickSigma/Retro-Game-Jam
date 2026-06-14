import pygame
import src.tileset as Tileset
from src.tileset import TileType, TILE_SIZE
from src.camera import Camera
from src.entities.entity import Entity, EntityType
from src.animator import Animator

class Jewel(Entity):
    # We got some bobbing goin on over here
    BOB_SPEED = 0.05
    BOB_HEIGHT = 2

    def __init__(self, x: int, y: int,):
        super().__init__(x,y, EntityType.JEWEL)
        self.pos = [float(x), float(y)]
        self.spawn_y = float(y)
        self._bob_timer = 0.0
        self.collected = False # flag so level.py knows to remove it

        self.animator = Animator(
            frames=[TileType.JEWEL.value],
            speed=20
        )

        self.COLLECTED_SFX = pygame.mixer.Sound("assets/sfx/collectable.wav")
        self.COLLECTED_SFX.set_volume(0.4)

    def update(self, player_rect: pygame.Rect):
        # So the jewels bob here 
        import math
        self._bob_timer += self.BOB_SPEED
        # never thought id ever use trigonometry again but here we are
        self.pos[1] = self.spawn_y + math.sin(self._bob_timer) * self.BOB_HEIGHT
        self.y = int(self.pos[1])

        # Check it player collected the jewel
        if self.rect.colliderect(player_rect):
            self.collected = True
            self.COLLECTED_SFX.play()
        
        self.animator.update()

    def draw(self, surface: pygame.Surface, camera: Camera):
        if self.collected:
            return
        camera_pos = camera.get_pos()
        frame = self.animator.get_frame()
        surface.blit(frame,(
            self.pos[0] - camera_pos[0],
            self.pos[1] - camera_pos[1]
        ))