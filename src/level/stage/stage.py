"""
Stage module for the game.

This handles the core logic of the game that puts everything
from the player, tiles, enemies, and so on, all together into one scene.

Most of the gameplay takes place here.
"""
from enum import Enum, unique, auto
import pygame

import src.tileset as Tileset
from src.camera import Camera, CameraState
from src.tiledmap import TiledMap
from src.player import Player

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

@unique
class MapTiles(Enum):
    NONE = 0
    BLOCK = 1
    RAMP_LEFT = 2
    RAMP_RIGHT = 3

class Stage:
    def __init__(self, surface: pygame.Surface, stage_no: tuple[int, int]):
        self.surface = surface
        self.stage_no = stage_no

        self.stage_folder = f"./assets/levels/{self.stage_no[0]}/{self.stage_no[1]}"

        """
        Every item in the game is dependant on the player's position,
        as it determines the camera viewport and scroll.
        """
        self.tilemap = TiledMap(f"{self.stage_folder}/stage.tmx")

        self.player = Player((0, 0))
        self.camera = Camera((0, 0), CameraState.HORIZONTAL, self.tilemap.size())
        self.viewport = pygame.Surface((32*8, 27*8))

        self.entities = None

        self.stage_banner = Tileset.render_string(f"Stage: {stage_no[0]}-{stage_no[1]}")

        self.restart()

        self.counter = 0

    def restart(self):
        """
        Restart the stage. 
        This basically sets up the initial state of the stage, so things like
        the player position, camera position and state, and any entities are loaded.
        """
        self.player.rect.x = 8*2
        self.player.rect.y = 22*8
        self.camera.pos = [0, 0]
        self.camera.state = self.camera.default_state
        

    def update(self) -> StageState:
        next_state = StageState.NO_CHANGE

        events = pygame.event.get()

        # Event handling can take place here
        for event in events:
            match event.type:
                case pygame.QUIT:
                    next_state = StageState.QUIT
                case pygame.KEYDOWN:
                    match event.key:
                        case pygame.K_ESCAPE:
                            next_state = StageState.QUIT
                        case pygame.K_SPACE:
                            # next_state = StageState.NEXT_STAGE
                            pass
                        case pygame.K_BACKSPACE:
                            next_state = StageState.RESTART_LEVEL

        self.player.update(events, self.tilemap.get_tiles("tiles"), self.tilemap.get_tiles("items"))

        self.camera.update(self.player.rect)

        self.surface.fill((0, 0, 0))
        Tileset.render_tile(self.surface, self.stage_banner, 0, 0)

        """Gameplay rendering"""
        self.viewport.fill((0, 0, 0))

        self.tilemap.draw_layer(self.viewport, self.camera, "tiles")
        self.tilemap.draw_layer(self.viewport, self.camera, "items")
        self.tilemap.draw_layer(self.viewport, self.camera, "background")

        self.player.draw(self.viewport, self.camera)

        self.surface.blit(self.viewport, (0, 8*3))

        return next_state
