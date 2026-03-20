from enum import Enum, auto, unique
import pygame
from math import sqrt

from src.camera import Camera
from src.tileset import TILE_SIZE, TileType
from src.tiledmap import Tiles

@unique
class PlayerState(Enum):
    """Used for handling the player states in its own internal state machine"""
    IDLE = auto()
    JUMPING = auto()

def collision_test(rect: pygame.Rect, tiles: Tiles) -> list[pygame.Rect]:
    hit_list = []
    for y in range(0, len(tiles)):
        for x in range(0, len(tiles[y])):
            if tiles[y][x].type == TileType.NONE:
                continue

            tile_rect = tiles[y][x].rect
            if rect.colliderect(tile_rect):
                hit_list.append(tile_rect)

    return hit_list

class Player:
    GRAVITY = 0.2
    MAX_MOMENTUM = 2
    VEL = 1
    JUMP_HEIGHT = 22  # Let the player jump 18 pixels (or just above 2 tiles)
    MAX_AIR_TIME = 6

    def __init__(self, pos):
        self.rect = pygame.Rect(pos[0], pos[1], 8, 8)

        # Variable related to player physics
        self.y_momentum = 0
        self.JUMP_VEL = sqrt(2*self.GRAVITY*self.JUMP_HEIGHT)  # Velocity when jumping

        self.moving_right = False
        self.moving_left = False
        self.air_time = 0

        self.state = PlayerState.IDLE
    
    def _handle_events(self, events: list[pygame.Event]):
        for event in events:
            match event.type:
                case pygame.KEYDOWN:
                    match event.key:
                        case pygame.K_LEFT:
                            self.moving_left = True
                        case pygame.K_RIGHT:
                            self.moving_right = True
                        case pygame.K_UP | pygame.K_SPACE:
                            if (not self.state == PlayerState.JUMPING) and self.air_time < self.MAX_AIR_TIME:
                                self.enter_jump_state()
                case pygame.KEYUP:
                    match event.key:
                        case pygame.K_LEFT:
                            self.moving_left = False
                        case pygame.K_RIGHT:
                            self.moving_right = False

    def move(self, movement: list[int], tiles: Tiles, items: Tiles) -> dict[str, bool]:
        collision_types = {'top': False, 'bottom': False, 'right': False, 'left': False}
        self.rect.x += movement[0]
        hit_list = collision_test(self.rect, tiles)
        for tile in hit_list:
            if movement[0] > 0:
                self.rect.right = tile.left
                collision_types['right'] = True
            elif movement[0] < 0:
                self.rect.left = tile.right
                collision_types['left'] = True
        self.rect.y += movement[1]
        hit_list = collision_test(self.rect, tiles)
        for tile in hit_list:
            if movement[1] > 0:
                self.rect.bottom = tile.top
                collision_types['bottom'] = True
            elif movement[1] < 0:
                self.rect.top = tile.bottom
                collision_types['top'] = True

        return collision_types


    def update(self, events: list[pygame.Event], tiles: Tiles, items: Tiles):
        self._handle_events(events)

        player_movement = [0, 0]

        if self.moving_left:
            player_movement[0] -= self.VEL
        elif self.moving_right:
            player_movement[0] += self.VEL

        player_movement[1] += self.y_momentum
        self.y_momentum += self.GRAVITY
        if self.y_momentum > self.MAX_MOMENTUM:
            self.y_momentum = self.MAX_MOMENTUM

        collisions = self.move(player_movement, tiles, items)

        if collisions["bottom"]:
            self.y_momentum = 0 
            self.state = PlayerState.IDLE
            self.air_time = 0
        else:
            self.air_time += 1

        if collisions["top"]:
            self.y_momentum = 0

    def draw(self, surface: pygame.Surface, camera: Camera):
        camera_pos = camera.get_pos()
        pygame.draw.rect(surface, (255, 0, 0), (self.rect.x - camera_pos[0], self.rect.y - camera_pos[1], 8, 8))


    """
    State machine related functions below:

    These functions are designed to simplify any property changes or setup when changing a state.   
    """
    def enter_jump_state(self):
        self.state = PlayerState.JUMPING
        self.y_momentum = -self.JUMP_VEL

