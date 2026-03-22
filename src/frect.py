import pygame

class FRect:
    """
    Floating point representation of a Rect as Pygame doesn't have one.
    """
    def __init__(self, x: float, y: float, w: int, h: int):
        self.x: float = x
        self.y: float = y
        self.w: int = w
        self.h: int = h

    def set_top(self, top: float):
        self.y = top
    def set_bottom(self, bottom: float):
        self.y = bottom - self.h
    def set_left(self, left: float):
        self.x = left
    def set_right(self, right: float):
        self.x = right - self.w
    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, self.y, self.w, self.h)