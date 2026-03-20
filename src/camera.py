"""
Camera module, handles the camera
"""
from enum import Enum, unique
import pygame

@unique
class CameraState(Enum):
    HORIZONTAL = 0
    VERTICAL = 1
    LOCKED_LEFT = 2
    LOCKED_RIGHT = 3

class Camera:
    WIDTH = 32*8
    HEIGHT = 27*8

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

    def update(self, target: list[int, int]):
        """Update the camera to follow a target"""
        # For now, we'll just follow the target as is without any special states
        self.pos[0] += (target[0] - self.pos[0] - (16*8))/20
        self.pos[1] += (target[1] - self.pos[1] - (13*8))/20

    def get_pos(self) -> tuple[int, int]:
        """Get the integer position of the camera"""
        return (int(self.pos[0]), int(self.pos[1]))

