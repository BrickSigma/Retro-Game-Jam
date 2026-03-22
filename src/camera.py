"""
Camera module, handles the camera
"""
from enum import Enum, unique
import pygame

from src.tileset import TILE_SIZE

@unique
class CameraState(Enum):
    HORIZONTAL = 0
    VERTICAL = 1

class Camera:
    WIDTH = 32*TILE_SIZE
    HEIGHT = 27*TILE_SIZE

    def __init__(self, pos: tuple[float, float], state: CameraState, stage_size: tuple[int, int]):
        """
        Parameters\n
        `pos` - initial position of the camera; this should be aligned to the screen\n
        `state` - initial state of the camera (i.e. horizontal or vertical)
        `stage_size` - tuple with the width and height of the stage in number of tiles
        """
        self.pos: list[float] = list(pos)
        self.state = CameraState.HORIZONTAL
        self.stage_size = stage_size

        self.default_state = CameraState.HORIZONTAL

    def update(self, target: pygame.Rect):
        """Update the camera to follow a target"""
        # For now, we'll just follow 5the target as is without any special states
        self.pos[0] += (target.x - self.pos[0] - (16*8))/20
        self.pos[1] += (target.y - self.pos[1] - (13*8))/20

        match self.state:
            case CameraState.HORIZONTAL:
                self.pos[1] = 0
                
                if self.pos[0] < 0:
                    self.pos[0] = 0
                elif self.pos[0] > (self.stage_size[0]*TILE_SIZE - self.WIDTH):
                    self.pos[0] = self.stage_size[0]*TILE_SIZE - self.WIDTH
            case CameraState.VERTICAL:
                self.pos[0] = 0

                if self.pos[1] < 0:
                    self.pos[1] = 0
                elif self.pos[1] > (self.stage_size[1]*TILE_SIZE - self.HEIGHT):
                    self.pos[1] = self.stage_size[1]*TILE_SIZE - self.HEIGHT

    def get_pos(self) -> tuple[int, int]:
        """Get the integer position of the camera"""
        return (int(self.pos[0]), int(self.pos[1]))

