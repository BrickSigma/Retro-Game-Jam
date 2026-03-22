from enum import Enum, auto, unique
import pygame
from math import sqrt

from src.camera import Camera
from src.tileset import TILE_SIZE, TileType
from src.tiledmap import Tiles
from src.animator import Animator

@unique
class PlayerState(Enum):
    """Used for handling the player states in its own internal state machine"""
    IDLE = auto()
    JUMPING = auto()
    MOVING = auto()
    FALLING = auto()
    SLIDING = auto()
    WALL_JUMP = auto()

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
    JUMP_HEIGHT = 18  # Let the player jump 18 pixels (or just above 2 tiles)
    MAX_AIR_TIME = 6
    MAX_WALL_JUMP_TIME = 34
    WALL_JUMP_HEIGHT = 16

    class CollisionTypes:
        def __init__(self):
            self.top = False
            self.bottom = False
            self.left = False
            self.right = False

    def __init__(self, pos):
        self.pos: list[float] = list(pos)
        self.rect = pygame.Rect(pos[0], pos[1], 8, 8)

        # Variable related to player physics
        self.y_momentum = 0
        self.JUMP_VEL = sqrt(2*self.GRAVITY*self.JUMP_HEIGHT)  # Velocity when jumping

        self.moving_right = False
        self.moving_left = False
        self.air_time = 0

        self.x_momentum = 0
        self.X_VEL = sqrt(2*self.GRAVITY*6)
        self.WALL_JUMP_VEL = sqrt(2*self.GRAVITY*self.WALL_JUMP_HEIGHT)
        self.wall_jump_right = True
        self.wall_jump_time = 1000

        self.facing_right = True

        self.state = PlayerState.IDLE

        # adding animation to player character
        self.animations = {
            PlayerState.IDLE: Animator(frames = [TileType.PLAYER_IDLE.value], speed = 20),
            PlayerState.JUMPING: Animator(frames = [TileType.PLAYER_ROPE_1.value], speed = 1),
            PlayerState.MOVING: Animator(frames = [
                TileType.PLAYER_RUN_1.value, 
                TileType.PLAYER_RUN_2.value, 
                TileType.PLAYER_RUN_3.value, 
                TileType.PLAYER_RUN_4.value
            ], speed = 6),
            PlayerState.FALLING: Animator(frames=[TileType.PLAYER_CLIMB_1.value, TileType.PLAYER_CLIMB_2.value], speed=8),
            PlayerState.SLIDING: Animator(frames = [TileType.SPIDER.value], speed = 20),
            PlayerState.WALL_JUMP: Animator(frames = [TileType.PLAYER_ROPE_1.value], speed = 1),
        }
    
    def _handle_events(self, events: list[pygame.Event]):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.moving_left = True
            self.facing_right = False
        else:
            self.moving_left = False
            self.facing_right = False
        if keys[pygame.K_RIGHT]:
            self.moving_right = True
            self.facing_right = True
        else:
            self.moving_right = False
            self.facing_right = False

        for event in events:
            match event.type:
                case pygame.KEYDOWN:
                    match event.key:
                        case pygame.K_UP | pygame.K_SPACE:
                            if (not self.state == PlayerState.JUMPING) and (not self.state == PlayerState.WALL_JUMP):
                                if self.state == PlayerState.SLIDING or self.wall_jump_time < self.MAX_AIR_TIME*3:
                                    self.enter_wall_jump_state()
                                elif self.air_time < self.MAX_AIR_TIME:
                                    self.enter_jump_state()
                        case pygame.K_p:
                            pass

    def move(self, movement: list[float], tiles: Tiles, items: Tiles) -> CollisionTypes:
        collision_types = self.CollisionTypes()
        self.pos[0] += movement[0]
        self.rect.x = self.pos[0]
        hit_list = collision_test(self.rect, tiles)
        for tile in hit_list:
            if movement[0] > 0:
                self.rect.right = tile.left
                self.pos[0] = self.rect.x
                collision_types.right = True
            elif movement[0] < 0:
                self.rect.left = tile.right
                self.pos[0] = self.rect.x
                collision_types.left = True

        # This keeps the player from leaving the horizontal boundary
        map_width_px = len(tiles[0]) * TILE_SIZE
        if self.rect.x < 0:
            self.rect.x = 0
            self.pos[0] = self.rect.x
        if (self.rect.x + self.rect.w) > map_width_px:
            self.rect.x = map_width_px - self.rect.w
            self.pos[0] = self.rect.x

        self.pos[1] += movement[1]
        self.rect.y = self.pos[1]
        hit_list = collision_test(self.rect, tiles)
        for tile in hit_list:
            if movement[1] > 0:
                self.rect.bottom = tile.top
                self.pos[1] = self.rect.y
                collision_types.bottom = True
            elif movement[1] < 0:
                self.rect.top = tile.bottom
                self.pos[1] = self.rect.y
                collision_types.top = True

        return collision_types
    
    def get_current_frame(self) -> pygame.Surface:
        """
        Get the current animation frame and flip it if the player is facing left
        """
        frame = self.animations[self.state].get_frame()
        if not self.facing_right:
            frame = pygame.transform.flip(frame, True, False)
        return frame

    def update(self, events: list[pygame.Event], tiles: Tiles, items: Tiles):
        self._handle_events(events)

        player_movement = [0, 0]

        # Handle jumping from a wall first
        if self.state == PlayerState.WALL_JUMP:
            player_movement[0] = self.x_momentum if self.wall_jump_right else -self.x_momentum
            self.x_momentum -= self.GRAVITY
            if self.x_momentum <= 0:
                self.change_state_to(PlayerState.JUMPING)
        else:
            if self.moving_left:
                player_movement[0] -= self.VEL
            elif self.moving_right:
                player_movement[0] += self.VEL

        player_movement[1] += self.y_momentum
        if not (self.state == PlayerState.SLIDING):
            self.y_momentum += self.GRAVITY
        if self.y_momentum > self.MAX_MOMENTUM:
            self.y_momentum = self.MAX_MOMENTUM

        collisions = self.move(player_movement, tiles, items)
        if collisions.bottom:
            self.y_momentum = 0.2
            self.air_time = 0
            if self.moving_left or self.moving_right:
                self.change_state_to(PlayerState.MOVING)
            else:
                self.change_state_to(PlayerState.IDLE)
        else:
            if collisions.left or collisions.right:
                if not self.state == PlayerState.MOVING:
                    self.change_state_to(PlayerState.SLIDING)
                    self.y_momentum = 0.2
            else:
                self.air_time += 1
                if self.y_momentum > 1 or self.state == PlayerState.SLIDING:
                    self.change_state_to(PlayerState.FALLING)

        self.wall_jump_time += 1

        if collisions.top:
            self.y_momentum = 0

    def draw(self, surface: pygame.Surface, camera: Camera):
        camera_pos = camera.get_pos()

        self.animations[self.state].update()
        frame = self.get_current_frame()
        surface.blit(frame, (self.rect.x - camera_pos[0], self.rect.y - camera_pos[1]))
        # pygame.draw.rect(surface, (255, 0, 0), (self.rect.x - camera_pos[0], self.rect.y - camera_pos[1], 8, 8))


    """
    State machine related functions below:

    These functions are designed to simplify any property changes or setup when changing a state.   
    """
    def enter_jump_state(self):
        self.change_state_to(PlayerState.JUMPING)
        self.y_momentum = -self.JUMP_VEL
        self.animations[self.state].reset()

    def enter_wall_jump_state(self):
        self.change_state_to(PlayerState.WALL_JUMP)
        self.x_momentum = self.X_VEL
        self.y_momentum = -self.WALL_JUMP_VEL
        self.animations[self.state].reset()

    def change_state_to(self, new_state: PlayerState):
        old_state = self.state
        self.state = new_state

        match new_state:
            case PlayerState.SLIDING:
                self.wall_jump_right = not self.facing_right

        # Handle anything to do with the previous state
        match old_state:
            case PlayerState.SLIDING:
                self.wall_jump_time = 0
