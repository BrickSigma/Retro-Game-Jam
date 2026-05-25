from enum import Enum, auto, unique
import pygame
from math import sqrt, sin, pi

from src.camera import Camera
from src.tileset import TILE_SIZE, TileType, get_tile, change_letter_color
from src.tiledmap import Tiles, Tile
from src.animator import Animator
from src.entities.entity import Entity, EntityType
from src.entities.ghost import GhostState
from src.guardian import GuardianState
from src.constants import FPS

@unique
class PlayerUpdateState(Enum):
    NO_CHANGE = auto()
    DIED = auto()
    COMPLETED_LEVEL = auto()

@unique
class PlayerState(Enum):
    """Used for handling the player states in its own internal state machine"""
    IDLE         = auto()
    JUMPING      = auto()
    MOVING       = auto()
    FALLING      = auto()
    SLIDING      = auto()
    WALL_JUMP    = auto()
    DEAD         = auto()
    CLIMBING     = auto()
    HANGING      = auto()
    HANGING_IDLE = auto()

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
    SWING_DURATION = 10
    CLIMB_VEL = 0.6
    HANG_VEL = 0.5 # I really don't want to understand how
    JUMP_HEIGHT = 10  # Let the player jump 15 pixels 
    BOUNCE_FORCE = 4.5
    MAX_AIR_TIME = 6
    MAX_WALL_JUMP_TIME = 36
    WALL_JUMP_HEIGHT = 14
    DEATH_DELAY = FPS*3
    INVULNERABILITY_DURATION = FPS * 2

    class CollisionTypes:
        def __init__(self):
            self.top = False
            self.bottom = False
            self.left = False
            self.right = False
            self.ladder = False
            self.chain = False
            self.chain_y = False

    def __init__(self, pos, stage_size: tuple[int, int]):
        self.pos: list[float] = list(pos)
        self.rect = pygame.Rect(pos[0], pos[1], 8, 8)
        self.stage_size = stage_size
        self.follow = None
        self._ladder_exit_timer = 0


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

        self._invulnerability_timer = 0

        self.in_web = False

        self._swing_timer  = 0
        self.sword_rect    = None
        self.wielding_sword  = False
        self.sword_swinging  = False

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
            PlayerState.CLIMBING: Animator(frames=[TileType.PLAYER_CLIMB_1.value, TileType.PLAYER_CLIMB_2.value], speed=8),
            PlayerState.HANGING: Animator(frames=[
                TileType.PLAYER_ROPE_1.value,
                TileType.PLAYER_ROPE_2.value,
                TileType.PLAYER_ROPE_3.value
            ], speed=15),
            PlayerState.HANGING_IDLE: Animator(frames=[
                TileType.PLAYER_ROPE_1.value,
            ], speed=1),
        }
    
    def _handle_events(self, events: list[pygame.Event]):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]:
            self.moving_left = True
            self.facing_right = False
        else:
            self.moving_left = False
        if keys[pygame.K_d]:
            self.moving_right = True
            self.facing_right = True
        else:
            self.moving_right = False
        
        self.climbing_up = keys[pygame.K_w]
        self.climbing_down = keys[pygame.K_s]

        for event in events:
            match event.type:
                case pygame.KEYDOWN:
                    match event.key:
                        case pygame.K_SPACE:
                            if self.in_web:
                                pass
                            elif self.state in (PlayerState.HANGING, PlayerState.HANGING_IDLE):
                                self.enter_jump_state()
                            elif (self.state != PlayerState.JUMPING) and (self.state != PlayerState.WALL_JUMP) and (self.state != PlayerState.CLIMBING):
                                if self.state == PlayerState.SLIDING or self.wall_jump_time < self.MAX_AIR_TIME*3:
                                    self.enter_wall_jump_state()
                                elif self.air_time < self.MAX_AIR_TIME:
                                    self.enter_jump_state()
                        case pygame.K_m:
                            if self.wielding_sword and not self.sword_swinging:
                                self.sword_swinging = True
                                self._swing_timer = self.SWING_DURATION

    def move(self, movement: list[float], tiles: Tiles, guardian_platform: pygame.Rect = None) -> CollisionTypes:
        flattened_tiles = [tile for row in tiles for tile in row]
        normal_tiles = [tile for tile in flattened_tiles
                         if tile.type != TileType.LADDER
                         and tile.type != TileType.CHAIN]
        ladders = [ladder for ladder in flattened_tiles if ladder.type == TileType.LADDER]
        chains = [chain for chain in flattened_tiles if chain.type == TileType.CHAIN]

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

        self._on_bounce_pad = False  # reset each frame
        for tile in hit_list:
            if movement[1] > 0:
                self.rect.bottom = tile.top
                self.pos[1] = self.rect.y
                collision_types.bottom = True
                # Check if this tile is the guardian bounce pad
                if guardian_platform and tile == guardian_platform:
                    self._on_bounce_pad = True
            elif movement[1] < 0:
                self.rect.top = tile.bottom
                self.pos[1] = self.rect.y
                collision_types.top = True
        
        # Handle ladder mechanics
        hit_list = collision_test(self.rect, ladders)
        if hit_list:
            collision_types.ladder = True
        
        chains =[tile for tile in flattened_tiles if tile.type == TileType.CHAIN]
        hit_list = collision_test(self.rect, chains)
        if hit_list:
            collision_types.chain = True
            collision_types.chain_y = hit_list[0].top
            
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

        # Check if player is in a web zone
        self.in_web = any(
            e.type == EntityType.WEB_ZONE and e.rect.colliderect(self.rect)
            for e in entities
        )
        # Apply web slow if inside web zone
        current_vel = self.VEL * 0.3 if self.in_web else self.VEL

        if self.state in  (PlayerState.HANGING, PlayerState.HANGING_IDLE):
            # No gravity while hanging
            player_movement[1] = 0
            self.y_momentum = 0
            if self.moving_left:
                player_movement[0] += self.HANG_VEL
                self.change_state_to(PlayerState.HANGING)
            elif self.moving_right:
                player_movement[0] -= self.HANG_VEL
                self.change_state_to(PlayerState.HANGING)
            else:
                self.change_state_to(PlayerState.HANGING_IDLE) 

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
                player_movement[0] -= current_vel
            elif self.moving_right:
                player_movement[0] += current_vel

        if self.state == PlayerState.CLIMBING:
            player_movement[0] = 0 # to ensure no horizontal movement while on the ladder 
            if self.climbing_up:
                player_movement[1] -= self.CLIMB_VEL
            elif self.climbing_down:
                player_movement[1] += self.CLIMB_VEL
        else:
            player_movement[1] += self.y_momentum
            if not (self.state == PlayerState.SLIDING):
                self.y_momentum += self.GRAVITY
            if self.y_momentum > self.MAX_MOMENTUM:
                self.y_momentum = self.MAX_MOMENTUM

        collisions = self.move(player_movement, tiles, guardian_platform)

        if self._ladder_exit_timer > 0:
            self._ladder_exit_timer -= 1

        if collisions.ladder:
            if self._ladder_exit_timer == 0:
                if self.climbing_up or self.climbing_down:
                    self.change_state_to(PlayerState.CLIMBING)
                    self.y_momentum = 0
                # If not pressing anything, don't change state — let running/idle continue
        else:
            if self.state == PlayerState.CLIMBING:
                self._ladder_exit_timer = 20  # block re-entry for 20 frames
                self.change_state_to(PlayerState.FALLING)
            elif collisions.bottom:
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
        
        # Chain entry — only when airborne
        if collisions.chain and self.state in (PlayerState.JUMPING, PlayerState.FALLING):
            self.change_state_to(PlayerState.HANGING_IDLE)
            # Snap player top to underside of chain
            self.pos[1] = collisions.chain_y + 3
            self.rect.y = int(self.pos[1])
            self.y_momentum = 0

        # Chain exit conditions
        if self.state in  (PlayerState.HANGING, PlayerState.HANGING_IDLE):
            if not collisions.chain:
                # Reached end of chain — drop
                self.change_state_to(PlayerState.FALLING)
            # Down key drops the player
            # (climbing_down reused since it's the same key)
            if self.climbing_down:
                self.change_state_to(PlayerState.FALLING)

        if self.state == PlayerState.CLIMBING and collisions.bottom:
            self.change_state_to(PlayerState.IDLE)
            self.y_momentum = 0

        if self.state == PlayerState.MOVING and not self.moving_left and not self.moving_right:
            self.change_state_to(PlayerState.IDLE)

        self.wall_jump_time += 1

        if collisions.top:
            self.y_momentum = 0

        if collisions.bottom:
            if self._on_bounce_pad and self.follow and self.follow.state == GuardianState.BOUNCE_PAD:
                # Launch player upward and destroy the pad
                self.y_momentum = -self.BOUNCE_FORCE
                self.change_state_to(PlayerState.JUMPING)
                self.follow.state = GuardianState.RETURNING
            else:
                self.y_momentum = 0.2
                self.air_time = 0
                if self.moving_left or self.moving_right:
                    self.change_state_to(PlayerState.MOVING)
                else:
                    self.change_state_to(PlayerState.IDLE)

        # Sword stab — independent of physics state so it never gets overridden
        if self.wielding_sword:
            if self.sword_swinging:
                self._swing_timer -= 1
                # Hitbox covers the full 120° arc beside the player
                if self.facing_right:
                    self.sword_rect = pygame.Rect(self.rect.right, self.rect.centery - TILE_SIZE, TILE_SIZE + 4, TILE_SIZE * 2)
                else:
                    self.sword_rect = pygame.Rect(self.rect.left - TILE_SIZE - 4, self.rect.centery - TILE_SIZE, TILE_SIZE + 4, TILE_SIZE * 2)
                if self._swing_timer <= 0:
                    self.sword_swinging = False
                    self.sword_rect = None
            else:
                self.sword_rect = None

            # Auto-exit when guardian drops SWORD state
            if not self.follow or self.follow.state != GuardianState.SWORD:
                self.wielding_sword = False
                self.sword_swinging = False
                self.sword_rect = None
        else:
            self.sword_rect = None

        # Check if the player has hit any entities
        gates = [e for e in entities if e.type == EntityType.GATE]
        if gates:
            if self.rect.colliderect(gates[0].rect):
                next_state = PlayerUpdateState.COMPLETED_LEVEL

        HARMFUL = {EntityType.SPIKE, EntityType.GHOST, EntityType.SPIDER}
        for entity in entities:
            if entity.type not in HARMFUL:
                continue
            if getattr(entity, 'distracted', False):
                continue  # enemy is chasing the decoy, passes through player
            if hasattr(entity, 'state') and entity.state in (GhostState.STUNNED, GhostState.DYING):
                continue
            if self.rect.colliderect(entity.rect):
                if self.follow and self.follow.shield_active:
                    # Shield absorbs the hit
                    self.follow.break_shield()
                    self._invulnerability_timer = self.INVULNERABILITY_DURATION
                    # Stun the ghost on contact if it's a ghost
                    if entity.type == EntityType.GHOST:
                        entity.state = GhostState.STUNNED
                        entity.stun_timer = entity.STUN_DURATION
                elif self._invulnerability_timer > 0:
                    pass  # still invulnerable
                else:
                    self.change_state_to(PlayerState.DEAD)
                break
        if self.rect.y + self.rect.h > self.stage_size[1]*TILE_SIZE:
            next_state = PlayerUpdateState.DIED

        return next_state

    def draw(self, surface: pygame.Surface, camera: Camera):
        camera_pos = camera.get_pos()

        self.animations[self.state].update()
        frame = self.get_current_frame()
        draw_x = self.rect.x - camera_pos[0]
        draw_y = self.rect.y - camera_pos[1]

        # Draw shield bubble around player if active
        if self.follow and self.follow.shield_active:
            pygame.draw.circle(
                surface,
                (100, 180, 255),
                (int(draw_x + self.rect.width // 2),
                int(draw_y + self.rect.height // 2)),
                10, 2  # radius 10, thickness 2
            )

        # Flicker player during invulnerability window
        if self._invulnerability_timer > 0:
            self._invulnerability_timer -= 1
            if self._invulnerability_timer % 6 < 3:
                return  # skip drawing every 3 frames to create flicker

        # Flicker during death delay
        if self.state == PlayerState.DEAD:
            if self.death_timer % 6 < 3:
                return

        surface.blit(frame, (draw_x, draw_y))

        if self.wielding_sword and self.follow:
            self._draw_sword_overlay(surface, draw_x, draw_y)

    def _draw_sword_overlay(self, surface: pygame.Surface, draw_x: int, draw_y: int):
        sword_tile = get_tile(TileType.SWORD.value)
        tint = self.follow.GOLD if self.follow.upgraded_l3 else self.follow.BLUE
        sword_tile = change_letter_color(sword_tile, tint)

        if self.facing_right:
            sword_tile = pygame.transform.flip(sword_tile, True, False)

        # Swing arc: 60° above horizontal → 60° below horizontal (120° total)
        if self.sword_swinging:
            progress = 1.0 - self._swing_timer / self.SWING_DURATION
            angle = 60 - progress * 120
        else:
            angle = 0  # hold horizontal

        _SCALE = 4
        big = pygame.transform.scale(sword_tile, (TILE_SIZE * _SCALE, TILE_SIZE * _SCALE))
        rotated_big = pygame.transform.rotate(big, angle)
        rotated = pygame.transform.scale(rotated_big, (rotated_big.get_width() // _SCALE, rotated_big.get_height() // _SCALE))

        # Pivot at the player's hand (just outside the player edge, vertically centred)
        if self.facing_right:
            cx = draw_x + TILE_SIZE + 2
        else:
            cx = draw_x - 2
        cy = draw_y + TILE_SIZE // 2

        surface.blit(rotated, (cx - rotated.get_width() // 2, cy - rotated.get_height() // 2))

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
            case PlayerState.CLIMBING:
                # Snap player to nearest tile center horizontally
                self.pos[0] = round(self.pos[0] / TILE_SIZE) * TILE_SIZE
                self.rect.x = int(self.pos[0])
            case PlayerState.SLIDING:
                self.wall_jump_right = not self.facing_right
            case PlayerState.DEAD:
                self.death_timer = 0

        # Handle anything to do with the previous state
        match old_state:
            case PlayerState.SLIDING:
                self.wall_jump_time = 0
