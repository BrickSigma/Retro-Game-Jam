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
        self.background: pygame.Surface = None
        self.width = 0  # Stage width in tiles
        self.height = 0 # Stage height in tiles
        self.tiles = None

        self.player = [0, 0]
        self.camera = Camera((0, 0), f"{self.stage_folder}/breakpoints.txt")
        self.viewport = pygame.Surface((32*8, 27*8))

        self.entities = None

        self.stage_banner = Tileset.render_string(f"Stage: {stage_no[0]}-{stage_no[1]}")

        self._load_stage()
        self.restart()

        self.counter = 0

    def _load_stage(self):
        """Load the stage data from its file"""            
        self.background = pygame.image.load(f"{self.stage_folder}/image.png")

        with open(f"{self.stage_folder}/tile-map.txt") as file:
            line = file.readline()
            line = line.split(" ")
            self.width = int(line[0])
            self.height = int(line[1])
            self.tiles = []
            
            for h in range(self.height):
                self.tiles.append([0]*self.width)
                row = file.readline().strip()
                row = row.split(",")
                for w in range(self.width):
                    tile = int(row[w])
                    self.tiles[h][w] = tile

    def restart(self):
        """
        Restart the stage. 
        This basically sets up the initial state of the stage, so things like
        the player position, camera position and state, and any entities are loaded.
        """
        self.player = [8*2, 22*8]
        self.camera.pos = [0, 0]
        self.camera.state = self.camera.default_state
        

    def update(self) -> StageState:
        next_state = StageState.NO_CHANGE

        # Event handling can take place here
        for event in pygame.event.get():
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
        
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.player[0] -= 1
        elif keys[pygame.K_RIGHT]:
            self.player[0] += 1
        if keys[pygame.K_UP]:
            self.player[1] -= 1
        elif keys[pygame.K_DOWN]:
            self.player[1] += 1

        self.camera.update(self.player)

        self.surface.fill((0, 0, 0))
        Tileset.render_tile(self.surface, self.stage_banner, 0, 0)

        camera_pos = self.camera.get_pos()

        self.viewport.fill((0, 0, 0))
        self.viewport.blit(self.background, self.camera.get_pos())
        pygame.draw.rect(self.viewport, (255, 0, 0), (self.player[0] + camera_pos[0], self.player[1] + camera_pos[1], 8, 8))

        self.surface.blit(self.viewport, (0, 8*3))

        return next_state