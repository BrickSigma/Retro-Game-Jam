from enum import Enum, auto, unique
import pygame
from math import sqrt

from src.camera import Camera
from src.tileset import TILE_SIZE, TileType
from src.tiledmap import Tiles, Tile
from src.animator import Animator
from src.entities.entity import Entity, EntityType
from src.entities.ghost import GhostState
from src.constants import FPS

@unique
class PlayerUpdateState(Enum):
    NO_CHANGE = auto()
    DIED = auto()
    COMPLETED_LEVEL = auto()

@unique
class PlayerState(Enum):
    """Used for handling the player states in its own internal state machine"""
    IDLE = auto()
    JUMPING = auto()
    MOVING = auto()
    FALLING = auto()
    SLIDING = auto()
    WALL_JUMP = auto()
    DEAD = auto()
    CLIMBING = auto()

def collision_test(rect: pygame.Rect, tiles: list[Tile]) -> list[pygame.Rect]:
    hit_list = []
    for tile in tiles:
        if tile.type == TileType.NONE:
            continue

        tile_rect = tile.rect
        if rect.colliderect(tile_rect):
            hit_list.append(tile_rect)

    return hit_list

class Player:
    GRAVITY = 0.2
    MAX_MOMENTUM = 2
    VEL = 1
    JUMP_HEIGHT = 10  # Let the player jump 15 pixels 
    MAX_AIR_TIME = 6
    MAX_WALL_JUMP_TIME = 36
    WALL_JUMP_HEIGHT = 14
    DEATH_DELAY = FPS*3

    class CollisionTypes:
        def __init__(self):
            self.top = False
            self.bottom = False
            self.left = False
            self.right = False
            self.ladder = False

    def __init__(self, pos, stage_size: tuple[int, int]):
        self.pos: list[float] = list(pos)
        self.rect = pygame.Rect(pos[0], pos[1], 8, 8)
        self.stage_size = stage_size
        self.follow = None


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

        self.death_timer = 0

        self.climbing_up = False
        self.climbing_down = False

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
            PlayerState.SLIDING: Animator(frames = [TileType.PLAYER_SLIDING.value], speed = 20),
            PlayerState.WALL_JUMP: Animator(frames = [TileType.PLAYER_ROPE_1.value], speed = 1),
            PlayerState.DEAD: Animator(frames=[TileType.PLAYER_DEAD.value], speed=1),
            PlayerState.CLIMBING: Animator(frames=[TileType.PLAYER_CLIMB_1.value, TileType.PLAYER_CLIMB_2.value], speed=8)
        }
    
    def _handle_events(self, events: list[pygame.Event]):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.moving_left = True
            self.facing_right = False
        else:
            self.moving_left = False
        if keys[pygame.K_RIGHT]:
            self.moving_right = True
            self.facing_right = True
        else:
            self.moving_right = False
        
        self.climbing_up = keys[pygame.K_UP]
        self.climbing_down = keys[pygame.K_DOWN]

        for event in events:
            match event.type:
                case pygame.KEYDOWN:
                    match event.key:
                        case pygame.K_SPACE:
                            if (self.state != PlayerState.JUMPING) and (self.state != PlayerState.WALL_JUMP) and (self.state != PlayerState.CLIMBING):
                                if self.state == PlayerState.SLIDING or self.wall_jump_time < self.MAX_AIR_TIME*3:
                                    self.enter_wall_jump_state()
                                elif self.air_time < self.MAX_AIR_TIME:
                                    self.enter_jump_state()

    def move(self, movement: list[float], tiles: Tiles, guardian_platform: pygame.Rect = None) -> CollisionTypes:
        flattened_tiles = [tile for row in tiles for tile in row]
        normal_tiles = [tile for tile in flattened_tiles if tile.type != TileType.LADDER]
        ladders = [ladder for ladder in flattened_tiles if ladder.type == TileType.LADDER]

        if self.follow:
            self.follow.path.append(self.rect.midbottom)

        collision_types = self.CollisionTypes()

        self.pos[0] += movement[0]
        self.rect.x = self.pos[0]
        hit_list = collision_test(self.rect, normal_tiles)

        if guardian_platform and self.rect.colliderect(guardian_platform):
            hit_list.append(guardian_platform)

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
        map_width_px = self.stage_size[0] * TILE_SIZE
        if self.rect.x < 0:
            self.rect.x = 0
            self.pos[0] = self.rect.x
        if (self.rect.x + self.rect.w) > map_width_px:
            self.rect.x = map_width_px - self.rect.w
            self.pos[0] = self.rect.x

        self.pos[1] += movement[1]
        self.rect.y = self.pos[1]
        hit_list = collision_test(self.rect, normal_tiles)

        if guardian_platform and self.rect.colliderect(guardian_platform):
                hit_list.append(guardian_platform)

        for tile in hit_list:
            if movement[1] > 0:
                self.rect.bottom = tile.top
                self.pos[1] = self.rect.y
                collision_types.bottom = True
            elif movement[1] < 0:
                self.rect.top = tile.bottom
                self.pos[1] = self.rect.y
                collision_types.top = True

        # Handle ladder mechanics
        hit_list = collision_test(self.rect, ladders)
        for tile in hit_list:
            if self.climbing_up or self.climbing_down:
                collision_types.ladder = True

        return collision_types
    
    
    
    def get_current_frame(self) -> pygame.Surface:
        """
        Get the current animation frame and flip it if the player is facing left
        """
        frame = self.animations[self.state].get_frame()
        if not self.facing_right:
            frame = pygame.transform.flip(frame, True, False)
        return frame

    def update(self, events: list[pygame.Event], tiles: Tiles, entities: list[Entity], guardian_platform=None) -> PlayerUpdateState:
        next_state = PlayerUpdateState.NO_CHANGE

        # If the player is dead, delay reseting the level using the timer
        if self.state == PlayerState.DEAD:
            self.death_timer += 1
            if self.death_timer > self.DEATH_DELAY:
                next_state = PlayerUpdateState.DIED
            return next_state

        # Get user input first
        self._handle_events(events)

        player_movement = [0, 0]

        # Handle jumping from a wall first
        # This is to prevent the player from instantly moving back to the wall after jumping from it.
        if self.state == PlayerState.WALL_JUMP:
            player_movement[0] = self.x_momentum if self.wall_jump_right else -self.x_momentum
            self.x_momentum -= self.GRAVITY
            if self.x_momentum <= 0:
                self.change_state_to(PlayerState.JUMPING)
        else:
            # Handle regular movement
            if self.moving_left:
                player_movement[0] -= self.VEL
            elif self.moving_right:
                player_movement[0] += self.VEL

        if self.state == PlayerState.CLIMBING:
            if self.climbing_up:
                player_movement[1] -= self.VEL
            elif self.climbing_down:
                player_movement[1] += self.VEL
        else:
            player_movement[1] += self.y_momentum
            if not (self.state == PlayerState.SLIDING):
                self.y_momentum += self.GRAVITY
            if self.y_momentum > self.MAX_MOMENTUM:
                self.y_momentum = self.MAX_MOMENTUM

        collisions = self.move(player_movement, tiles, guardian_platform)

        if collisions.ladder:
            self.change_state_to(PlayerState.CLIMBING)
        else:
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

        # Check if the player has hit any entities
        gates = [e for e in entities if e.type == EntityType.GATE]
        if gates:
            if self.rect.colliderect(gates[0].rect):
                next_state = PlayerUpdateState.COMPLETED_LEVEL

        HARMFUL = {EntityType.SPIKE, EntityType.GHOST}
        for entity in entities:
            if entity.type not in HARMFUL:
                continue
            if hasattr(entity, 'state') and entity.state  in (GhostState.STUNNED, GhostState.DYING):
                continue
            if self.rect.colliderect(entity.rect):
                self.change_state_to(PlayerState.DEAD)
                break

        if self.rect.y + self.rect.h > self.stage_size[1]*TILE_SIZE:
            next_state = PlayerUpdateState.DIED

        return next_state

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

        # Handle anything to do with the new state
        match new_state:
            case PlayerState.SLIDING:
                self.wall_jump_right = not self.facing_right
            case PlayerState.DEAD:
                self.death_timer = 0

        # Handle anything to do with the previous state
        match old_state:
            case PlayerState.SLIDING:
                self.wall_jump_time = 0
