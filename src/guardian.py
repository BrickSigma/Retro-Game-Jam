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
    FOLLOWING = auto() # trailing the player normally
    PLATFORM = auto() # frozen solid, Player can stand on it
    RETURNING = auto() # platform expired, floating back to player 

class Guardian:

    PATH_MAX = 20 # frames behind the player
    PLATFORM_DURATION = FPS * 3 # 3 seconds at 60fps = 180 frames
    RETURN_SPEED = 2.0 # how fast guardian float back after platform expires

    def __init__(self, player, pos: tuple[int, int]):
        self.rect = pygame.Rect(pos[0], pos[1], 8, 8)
        self.pos = [float(pos[0]), float(pos[1])]
        self.path: list[tuple[int,int]] = []
        self.state = GuardianState.FOLLOWING

        self._platform_timer = 0
        self._player_ref = player

        self.animations = {
            GuardianState.FOLLOWING: Animator(frames=[TileType.GUARDIAN_IDLE.value], speed=20),
            GuardianState.PLATFORM: Animator(frames=[TileType.PLATFORM.value], speed=10),
            GuardianState.RETURNING: Animator(frames=[TileType.GUARDIAN_IDLE.value], speed=15)
        }

        player.follow = self
    
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
        self.path.clear()  # clear path so it doesn't snap back when returning

        return True  # charge spent

    def update(self):
        match self.state:
            case GuardianState.FOLLOWING:
                # Original path following behaviour
                if len(self.path) > self.PATH_MAX:
                    new_pos = self.path.pop(0)
                    self.rect.midbottom = new_pos
                    self.pos = [float(self.rect.x), float(self.rect.y)]

            case GuardianState.PLATFORM:
                # Count down platform duration
                self._platform_timer -= 1
                if self._platform_timer <= 0:
                    self.path.clear()
                    self.state = GuardianState.RETURNING

            case GuardianState.RETURNING:
                # Float back toward player
                player_rect = self._player_ref.rect
                dx = player_rect.centerx - self.rect.centerx
                dy = player_rect.centery - self.rect.centery
                distance = (dx**2 + dy**2) ** 0.5

                if distance < TILE_SIZE:
                    # Close enough — resume following
                    self.path.clear()
                    self.state = GuardianState.FOLLOWING
                else:
                    # Normalised movement toward player
                    self.pos[0] += (dx / distance) * self.RETURN_SPEED
                    self.pos[1] += (dy / distance) * self.RETURN_SPEED
                    self.rect.x = int(self.pos[0])
                    self.rect.y = int(self.pos[1])

        self.animations[self.state].update()

    def draw(self, surface: pygame.Surface, camera: Camera):
        camera_pos = camera.get_pos()
        frame = self.animations[self.state].get_frame()

        # Flash the platform when it's about to expire (last 60 frames = 1 second)
        if self.state == GuardianState.PLATFORM:
            if self._platform_timer < FPS and self._platform_timer % 10 < 5:
                return  # skip drawing every 5 frames to create flicker effect

        surface.blit(frame, (
            self.rect.x - camera_pos[0],
            self.rect.y - camera_pos[1]
        ))

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
        return Projectile(x, y, facing_right)
    