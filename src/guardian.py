import pygame
import src.tileset as Tileset
from src.camera import Camera
from src.tileset import TILE_SIZE, TileType
class Guardian:

    PATH_MAX = 20

    def __init__(self, player, pos: tuple[int, int]):
        self.rect = pygame.Rect(pos[0], pos[1], 8, 8)
        self.path: list[tuple[int,int]] = []
        player.follow = self

    def update(self):
        if len(self.path) > self.PATH_MAX:
            self.rect.midbottom = self.path.pop(0)

    def draw(self, surface: pygame.Surface, camera: Camera):
        camera_pos = camera.get_pos()
        frame = Tileset.get_tile(TileType.GUARDIAN_IDLE.value)
        surface.blit(frame,(self.rect.x - camera_pos[0], self.rect.y - camera_pos[1]))