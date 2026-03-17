"""
Level module.

Handles loading level files and the stages within a level.
"""
from enum import Enum, unique, auto
import pygame

from src.level.stage import Stage, StageState

@unique
class LevelState(Enum):
    NO_CHANGE = auto()
    NEXT_LEVEL = auto()  # Move to the next level
    QUIT = auto()

class Level:
    def __init__(self, surface: pygame.Surface, level_no: int):
        self.surface = surface
        self.level_no = level_no

        self.stage = Stage(surface, (self.level_no, 1))

        self.current_stage = 1

    def restart(self):
        """Restart the level"""
        self.current_stage = 1
        self.stage = Stage(self.surface, (self.level_no, 1))

    def next_stage(self):
        """Move to the next stage"""
        self.current_stage += 1
        self.stage = Stage(self.surface, (self.level_no, self.current_stage))

    def update(self) -> LevelState:
        next_state = LevelState.NO_CHANGE

        match self.stage.update():
            case StageState.QUIT:
                next_state = LevelState.QUIT
            case StageState.NEXT_STAGE:
                if (self.current_stage + 1) > 3:
                    next_state = LevelState.NEXT_LEVEL
                else:
                    self.next_stage()
            case StageState.RESTART_LEVEL:
                self.restart()
            case StageState.NO_CHANGE:
                pass

        return next_state