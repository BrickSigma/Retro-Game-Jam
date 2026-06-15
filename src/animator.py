# for any animations
import pygame
import src.tileset as Tileset

class Animator:
    def __init__(self, frames: list[int], speed: int):
        self.frames = frames
        self.speed = speed
        self._counter = 0
        self._index = 0

    """ 
    frames = list of the tile indices from the tileset
    speed = how many game frames to show each title before advancing
    """

    def update(self):
        self._counter += 1
        if self._counter >= self.speed:
            self._counter = 0
            self._index = (self._index + 1) % len(self.frames)
    
    def reset(self):
        self._counter = 0
        self._index = 0

    def get_frame(self) -> pygame.Surface:
        return Tileset.get_tile(self.frames[self._index])