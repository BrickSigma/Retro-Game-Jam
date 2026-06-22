from abc import ABC, abstractmethod
from enum import Enum, unique, auto
import pygame

@unique
class SceneState(Enum):
    NO_CHANGE = auto()
    MENU = auto()
    CONTROLS = auto()
    GAME = auto()
    CREDITS = auto()
    GAME_OVER = auto()
    """Quit the game"""

class Scene(ABC):
    """
    Scene class that handles things like menus, the game loop, 
    and general state management in the game.
    """
    def __init__(self, surface: pygame.Surface):
        """
        `surface` - the surface to render to
        """
        self.surface = surface

    @abstractmethod
    def update(self, events: list[pygame.Event]) -> SceneState:
        """
        Function that runs every frame in the game loop.

        Returns an int indicating the next scene to go to.
        """
        pass