"""
Stage module for the game.

This handles the core logic of the game that puts everything
from the player, tiles, enemies, and so on, all together into one scene.

Most of the gameplay takes place here.
"""
from enum import Enum, unique, auto
import pygame

import src.tileset as Tileset

"""
INTERNAL NOTES:
A level consists of stages, specifically 3 for this game.

Each stage has the following components:
    1. Background layer with non-interactable tiles
    2. Tile/platform layer used for walking on
    3. Items/collectables/enemies/other entities layer
    4. The player camera
"""

@unique
class StageState(Enum):
    NO_CHANGE = auto()
    NEXT_STAGE = auto()     # Moves onto the next stage
    RESTART_LEVEL = auto()  # Restarts the whole level if the player lost all lives
    QUIT = auto()

class Stage:
    WIDTH = 32*3
    HEIGHT = 30*2

    def __init__(self, surface: pygame.Surface, stage_no: tuple[int, int]):
        self.surface = surface
        self.stage_no = stage_no

        """
        Every item in the game is dependant on the player's position,
        as it determines the camera viewport and scroll.
        """
        self.player = None
        self.background = None
        self.tiles = None
        self.entities = None

        self.stage_banner = Tileset.render_string(f"Stage: {stage_no[0]}-{stage_no[1]}")

    def load_stage(self):
        """Load the stage data from its file"""
        pass

    def restart(self):
        """Restart the stage"""
        pass

    def update(self) -> StageState:
        next_state = StageState.NO_CHANGE

        # Event handling can take place here
        for event in pygame.event.get():
            match event.type:
                case pygame.QUIT:
                    next_state = StageState.QUIT
                case pygame.KEYDOWN:
                    match event.key:
                        case pygame.K_SPACE:
                            next_state = StageState.NEXT_STAGE
                        case pygame.K_BACKSPACE:
                            next_state = StageState.RESTART_LEVEL

        self.surface.fill((0, 0, 0))
        Tileset.render_tile(self.surface, self.stage_banner, 0, 0)

        pygame.draw.rect(self.surface, (255, 0, 0), (0, 3*8, 32*8, 27*8))

        return next_state