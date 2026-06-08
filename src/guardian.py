import math
import pygame
import src.tileset as Tileset
from src.camera import Camera
from src.tileset import TILE_SIZE, TileType
from src.animator import Animator
from src.constants import FPS
from src.entities.projectile import Projectile
from enum import Enum, auto, unique

@unique
class GuardianState(Enum):
    FOLLOWING  = auto()
    PLATFORM   = auto()
    BOUNCE_PAD = auto()
    RETURNING  = auto()
    SWORD      = auto()
    DECOY      = auto()

class Guardian:

    HOVER_OFFSET_X = 12  # pixels to the side of the player (direction-aware)
    HOVER_OFFSET_Y = -10  # pixels above the player
    FOLLOW_SPEED = 0.06  # lerp factor per frame (0 = never moves, 1 = instant snap)
    BOB_AMPLITUDE = 2.0  # pixels of vertical sine-wave float
    BOB_SPEED = 0.05     # radians per frame
    PLATFORM_DURATION = FPS * 3
    RETURN_SPEED = 2.0
    FLASH_DURATION = FPS * 3
    BOUNCE_FORCE = 4.5
    SWORD_DURATION = FPS * 4
    DECOY_DURATION = FPS * 3

    BLUE = (0,150,255)
    GOLD = (255,215,0)


    def __init__(self, player, pos: tuple[int, int]):
        self.rect = pygame.Rect(pos[0], pos[1], 8, 8)
        self.pos = [float(pos[0]), float(pos[1])]
        self.state = GuardianState.FOLLOWING
        self._bob_timer = 0.0

        self._platform_timer = 0
        self._player_ref = player

        self.animations = {
            GuardianState.FOLLOWING:  Animator(frames=[TileType.FIRE.value],         speed=20),
            GuardianState.PLATFORM:   Animator(frames=[TileType.PLATFORM.value],     speed=10),
            GuardianState.BOUNCE_PAD: Animator(frames=[TileType.SPRING.value],       speed=10),
            GuardianState.RETURNING:  Animator(frames=[TileType.FIRE.value],         speed=15),
            GuardianState.SWORD:      Animator(frames=[TileType.SWORD.value],        speed=1),
            GuardianState.DECOY:      Animator(frames=[
                TileType.PLAYER_RUN_1.value,
                TileType.PLAYER_RUN_2.value,
                TileType.PLAYER_RUN_3.value,
                TileType.PLAYER_RUN_4.value,
            ], speed=6),
        }

        player.follow = self

        # Level 2 upgrade flags
        self.upgraded_l2    = False
        self.can_shield     = False
        self.can_bounce_pad = False

        # Level 3 upgrade flags
        self.upgraded_l3    = False
        self.can_use_sword  = False
        self.can_use_decoy  = False

        self.shield_active  = False
        self.flash_timer    = 0
        self.flash_color    = self.BLUE

        self._sword_timer        = 0
        self._decoy_timer        = 0
        self._decoy_pos          = [0.0, 0.0]
        self._decoy_y_vel        = 0.0
        self._decoy_ground_y     = 0.0
        self._decoy_spawn_x      = 0.0
        self._decoy_facing_right = True

        # SFX
        self.FIRE_SFX = pygame.mixer.Sound("assets/sfx/fire.mp3")
        self.FIRE_SFX.set_volume(0.4)
    
    def _get_platform_pos(self, player_rect: pygame.Rect, facing_right: bool, player_airborne: bool, player_vel: list) -> tuple[int, int]:
        """
        Project platform position ahead of the player snapped to tile grid.
        Places platform 2 tiles ahead in the direction the player is facing.
        """
        if player_airborne:
            # Predict landing position based on current velocity
            # Project forward a few frames to estimate trajectory
            LOOK_AHEAD = 15  # frames to look ahead
            
            predicted_x = player_rect.centerx + (player_vel[0] * LOOK_AHEAD)
            predicted_y = player_rect.bottom + (player_vel[1] * LOOK_AHEAD)

            # Snap to grid
            x = round(predicted_x / TILE_SIZE) * TILE_SIZE - TILE_SIZE // 2
            y = round(predicted_y / TILE_SIZE) * TILE_SIZE
        else:
            offset = 2 * TILE_SIZE
            if facing_right:
                x = player_rect.right + offset
            else:
                x = player_rect.left - offset - TILE_SIZE
            x = round(x / TILE_SIZE) * TILE_SIZE
            y = round(player_rect.top / TILE_SIZE) * TILE_SIZE

        return (x, y)
    
    def activate_platform(self, player_rect: pygame.Rect, facing_right: bool, player_airborne: bool, player_vel: list) -> bool:
        """
        Attempt to activate the platform ability.
        Returns True if activated (charge should be spent), False if already active.
        """
        if self.state != GuardianState.FOLLOWING:
            return False  # already a platform or returning, don't spend charge

        x, y = self._get_platform_pos(player_rect, facing_right, player_airborne,player_vel)

        # Snap guardian to platform position
        self.pos  = [float(x), float(y)]
        self.rect.x = x
        self.rect.y = y

        self.state = GuardianState.PLATFORM
        self._platform_timer = self.PLATFORM_DURATION
        return True  # charge spent
    
    def trigger_upgrade(self):
        """Level 2 upgrade — blue tint, unlocks shield and bounce pad"""
        self.upgraded_l2    = True
        self.flash_timer    = self.FLASH_DURATION
        self.flash_color    = self.BLUE
        self.can_shield     = True
        self.can_bounce_pad = True

    def trigger_level3_upgrade(self):
        """Level 3 upgrade — gold tint, unlocks sword and decoy"""
        self.upgraded_l3   = True
        self.flash_timer   = self.FLASH_DURATION
        self.flash_color   = self.GOLD
        self.can_use_sword = True
        self.can_use_decoy = True

    def activate_sword(self) -> bool:
        """Transform Guardian into a sword. Returns True if a charge should be spent."""
        if self.state != GuardianState.FOLLOWING:
            return False
        if not self.can_use_sword:
            return False
        self.state = GuardianState.SWORD
        self._sword_timer = self.SWORD_DURATION
        return True

    def activate_decoy(self) -> bool:
        """Detach Guardian as a decoy that patrols the ground. Returns True if a charge should be spent."""
        if self.state != GuardianState.FOLLOWING:
            return False
        if not self.can_use_decoy:
            return False
        self.state = GuardianState.DECOY
        self._decoy_timer        = self.DECOY_DURATION
        self._decoy_pos          = [float(self.rect.x), float(self.rect.y)]
        self._decoy_y_vel        = 0.0
        self._decoy_ground_y     = float(self._player_ref.rect.y)
        self._decoy_spawn_x      = float(self.rect.x)
        self._decoy_facing_right = self._player_ref.facing_right
        return True


    def update(self):
        match self.state:
            case GuardianState.FOLLOWING:
                self._bob_timer += self.BOB_SPEED
                player_rect = self._player_ref.rect
                side = 1 if self._player_ref.facing_right else -1
                target_x = player_rect.centerx + side * self.HOVER_OFFSET_X - self.rect.width // 2
                target_y = player_rect.centery + self.HOVER_OFFSET_Y + math.sin(self._bob_timer) * self.BOB_AMPLITUDE
                self.pos[0] += (target_x - self.pos[0]) * self.FOLLOW_SPEED
                self.pos[1] += (target_y - self.pos[1]) * self.FOLLOW_SPEED
                self.rect.x = int(self.pos[0])
                self.rect.y = int(self.pos[1])

            case GuardianState.PLATFORM:
                # Count down platform duration
                self._platform_timer -= 1
                if self._platform_timer <= 0:
                    self.state = GuardianState.RETURNING

            case GuardianState.BOUNCE_PAD:
                self._platform_timer -= 1
                if self._platform_timer <= 0:
                    self.state = GuardianState.RETURNING

            case GuardianState.RETURNING:
                player_rect = self._player_ref.rect
                dx = player_rect.centerx - self.rect.centerx
                dy = player_rect.centery - self.rect.centery
                distance = (dx**2 + dy**2) ** 0.5

                if distance < TILE_SIZE:
                    self.state = GuardianState.FOLLOWING
                else:
                    self.pos[0] += (dx / distance) * self.RETURN_SPEED
                    self.pos[1] += (dy / distance) * self.RETURN_SPEED
                    self.rect.x = int(self.pos[0])
                    self.rect.y = int(self.pos[1])

            case GuardianState.SWORD:
                player_rect = self._player_ref.rect
                offset_x = 10 if self._player_ref.facing_right else -10
                self.rect.x = player_rect.x + offset_x
                self.rect.y = player_rect.y
                self.pos = [float(self.rect.x), float(self.rect.y)]

                self._sword_timer -= 1
                if self._sword_timer <= 0:
                    self.state = GuardianState.RETURNING

            case GuardianState.DECOY:
                PATROL_SPEED = 0.5
                PATROL_RANGE = 3 * TILE_SIZE

                # Gravity — fall until hitting ground level
                self._decoy_y_vel = min(self._decoy_y_vel + 0.3, 3.0)
                self._decoy_pos[1] = min(self._decoy_pos[1] + self._decoy_y_vel, self._decoy_ground_y)
                if self._decoy_pos[1] >= self._decoy_ground_y:
                    self._decoy_y_vel = 0.0

                # Left/right patrol, flip direction at boundaries
                patrol_dir = 1 if self._decoy_facing_right else -1
                self._decoy_pos[0] += PATROL_SPEED * patrol_dir
                if self._decoy_pos[0] >= self._decoy_spawn_x + PATROL_RANGE:
                    self._decoy_facing_right = False
                elif self._decoy_pos[0] <= self._decoy_spawn_x - PATROL_RANGE:
                    self._decoy_facing_right = True

                self.rect.x = int(self._decoy_pos[0])
                self.rect.y = int(self._decoy_pos[1])
                self.pos = [float(self.rect.x), float(self.rect.y)]

                self._decoy_timer -= 1
                if self._decoy_timer <= 0:
                    self.state = GuardianState.RETURNING

        self.animations[self.state].update()

    def draw(self, surface: pygame.Surface, camera: Camera):
        camera_pos = camera.get_pos()
        frame = self.animations[self.state].get_frame()

        # Flash the platform when it's about to expire (last 60 frames = 1 second)
        if self.state == GuardianState.PLATFORM:
            if self._platform_timer < FPS and self._platform_timer % 10 < 5:
                return  # skip drawing every 5 frames to create flicker effect
            
        # Sword is rendered as a player overlay in player.py
        if self.state == GuardianState.SWORD:
            return

        # Decoy — red-tinted player sprite with run animation
        if self.state == GuardianState.DECOY:
            frame = self.animations[self.state].get_frame()
            frame = Tileset.change_letter_color(frame, self.GOLD)
            if not self._decoy_facing_right:
                frame = pygame.transform.flip(frame, True, False)
            surface.blit(frame, (self.rect.x - camera_pos[0], self.rect.y - camera_pos[1]))
            return

        # Upgrade flash — uses flash_color set by whichever upgrade triggered it
        if self.flash_timer > 0:
            self.flash_timer -= 1
            if (self.flash_timer // 8) % 2 == 0:
                frame = Tileset.change_letter_color(frame, self.flash_color)
        elif self.upgraded_l3:
            frame = Tileset.change_letter_color(frame, self.GOLD)
        elif self.upgraded_l2:
            frame = Tileset.change_letter_color(frame, self.BLUE)

        surface.blit(frame, (
            self.rect.x - camera_pos[0],
            self.rect.y - camera_pos[1]
        ))
    
    def activate_shield(self) -> bool:
        if not self.can_shield:
            return False
        if self.shield_active:
            return False  # already shielded
        self.shield_active = True
        return True

    def break_shield(self):
        """Called when shield absorbs a hit"""
        self.shield_active = False

    def activate_bounce_pad(self, player_rect: pygame.Rect, facing_right: bool, player_airborne: bool, player_vel: list) -> bool:
        if self.state != GuardianState.FOLLOWING:
            return False
        if not self.can_bounce_pad:  # gated behind upgrade
            return False

        if player_airborne:
            # Spawn directly below player
            x = round(player_rect.centerx / TILE_SIZE) * TILE_SIZE - TILE_SIZE // 2
            y = round((player_rect.bottom + TILE_SIZE) / TILE_SIZE) * TILE_SIZE
        else:
            # Spawn ahead of player
            x, y = self._get_platform_pos(player_rect, facing_right, player_airborne, player_vel)

        self.pos = [float(x), float(y)]
        self.rect.x = x
        self.rect.y = y
        self.state = GuardianState.BOUNCE_PAD
        self._platform_timer = FPS * 3  # disappears after 3 seconds or first bounce
        return True

    def fire_projectile(self, player_rect: pygame.Rect, facing_right: bool) -> 'Projectile':
        """
        Fire a projectile from the Guardian's current position.
        Returns the projectile so level.py can add it to entities.
        """
        if self.state != GuardianState.FOLLOWING:
            return None
        # Spawn at guardian center
        x = self.rect.centerx - TILE_SIZE // 2
        y = self.rect.centery - TILE_SIZE // 2

        # Play SFX as well
        self.FIRE_SFX.play()
        return Projectile(x, y, facing_right)
    