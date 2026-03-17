"""
Game scene module: this holds the actual playable game.
"""

from src.scenes import Scene, SceneState
import src.tileset as Tileset
import pygame
from src.level import Level, LevelState

class Game(Scene):
    def __init__(self, surface):
        super().__init__(surface)
        self.text = Tileset.render_string("Main Game")

        self.level = Level(self.surface, 1)
        self.current_level = 1

    def next_level(self):
        """Move to the next level"""
        self.current_level += 1
        self.level = Level(self.surface, self.current_level)

    def update(self):
        """Main game loop sits here"""
        next_state = SceneState.NO_CHANGE

        match self.level.update():
            case LevelState.QUIT:
                next_state = SceneState.QUIT
            case LevelState.NEXT_LEVEL:
                if (self.current_level + 1) > 5:
                    next_state = SceneState.CREDITS
                else:
                    self.next_level()
            case LevelState.NO_CHANGE:
                pass

        return next_state