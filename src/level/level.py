"""
Level module for the game.

This handles the core logic of the game that puts everything
from the player, tiles, enemies, and so on, all together into one scene.

Most of the gameplay takes place here.
"""
from enum import Enum, unique, auto
import pygame

import src.tileset as Tileset
from src.camera import Camera, CameraState
from src.tiledmap import TiledMap
from src.player import Player, PlayerUpdateState, PlayerState
from src.entities.entity import Entity, EntityType

"""
INTERNAL NOTES:
Each level has the following components:
    1. Background layer with non-interactable tiles
    2. Tile/platform layer used for walking on
    3. Items/collectables/enemies/other entities layer
    4. The player camera
"""

@unique
class LevelState(Enum):
    NO_CHANGE = auto()
    NEXT_LEVEL = auto()     # Moves onto the next level
    QUIT = auto()

@unique
class MapTiles(Enum):
    NONE = 0
    BLOCK = 1
    RAMP_LEFT = 2
    RAMP_RIGHT = 3

class Level:
    LAYER_PLATFORM   = "platform"   # solid tiles the player walks on
    LAYER_ITEMS      = "items"      # collectibles and interactables (optional)
    LAYER_BACKGROUND = "background" # non-collidable backdrop tiles (optional)

    def __init__(self, surface: pygame.Surface, level_no: int, camera_type: CameraState = CameraState.HORIZONTAL):
        self.surface = surface
        self.level_no = level_no

        self.level_folder = f"./assets/levels/{self.level_no}"

        """
        Every item in the game is dependant on the player's position,
        as it determines the camera viewport and scroll.
        """
        self.tilemap = TiledMap(f"{self.level_folder}/level.tmx")

        self.entities = self.tilemap.get_entities()

        self.player_start: Entity = None
        self.player = Player((0, 0), self.tilemap.size())

        player_index = -1
        for i in range(len(self.entities)):
            entity = self.entities[i]
            if entity.type == EntityType.PLAYER:
                player_index = i
                self.player_start = entity
                break

        self.entities.pop(player_index)

        self.restart()

        self.camera = Camera((self.player.pos[0], self.player.pos[1]), camera_type, self.tilemap.size())
        self.viewport = pygame.Surface((32*8, 27*8))

        self.level_banner = Tileset.render_string(f"Level: {level_no}")

    def restart(self):
        """
        Restart the level. 
        This basically sets up the initial state of the level, so things like
        the player position, camera position and state, and any entities are loaded.
        """
        self.player.pos = [self.player_start.x, self.player_start.y]
        self.player.rect.x = self.player_start.x
        self.player.rect.y = self.player_start.y
        self.player.state = PlayerState.IDLE
    
    def update(self) -> LevelState:
        next_state = LevelState.NO_CHANGE

        events = pygame.event.get()

        # Event handling can take place here
        for event in events:
            match event.type:
                case pygame.QUIT:
                    next_state = LevelState.QUIT
                case pygame.KEYDOWN:
                    match event.key:
                        case pygame.K_ESCAPE:
                            next_state = LevelState.QUIT
                        case pygame.K_BACKSPACE:
                            self.restart()

        tiles_rect = pygame.Rect(
            (self.player.rect.x//Tileset.TILE_SIZE) - 1, 
            (self.player.rect.y//Tileset.TILE_SIZE) - 1, 
            4, 
            4)
        adjecent_tiles = self.tilemap.get_tiles_rect(tiles_rect, self.LAYER_PLATFORM)
        player_state = self.player.update(
            events, 
            adjecent_tiles, 
            self.entities
        )

        match player_state:
            case PlayerUpdateState.NO_CHANGE:
                pass
            case PlayerUpdateState.DIED:
                self.restart()
            case PlayerUpdateState.COMPLETED_LEVEL:
                next_state = LevelState.NEXT_LEVEL

        self.camera.update(self.player.rect)

        self.surface.fill((0, 0, 0))
        Tileset.render_tile(self.surface, self.level_banner, 0, 0)

        """Gameplay rendering"""
        self.viewport.fill((0, 0, 0))

        self.tilemap.draw_layer(self.viewport, self.camera, self.LAYER_BACKGROUND, (128, 128, 128))
        self.tilemap.draw_layer(self.viewport, self.camera, self.LAYER_PLATFORM)

        for entity in self.entities:
            entity.draw(self.viewport, self.camera)

        self.player.draw(self.viewport, self.camera)

        self.surface.blit(self.viewport, (0, 8*3))

        return next_state
