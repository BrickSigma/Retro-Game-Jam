import pygame
import math
import src.tileset as Tileset
from src.tileset import TileType, TILE_SIZE
from src.camera import Camera
from src.entities.entity import Entity, EntityType
from src.animator import Animator
from src.constants import FPS
from enum import Enum, auto, unique

@unique
class SpiderState(Enum):
    HANGING  = auto()  # clings to ceiling, waiting
    AIMING   = auto()  # player in range, tracking and firing
    CHASING  = auto()  # web hit player, descending fast
    DEAD     = auto()  # hit by projectile, flickering out

class Spider(Entity):
    DETECT_RADIUS = 7 * TILE_SIZE   # detection range in pixels
    CHASE_SPEED   = 1.2             # faster than ghost (0.8)
    FIRE_COOLDOWN = FPS * 3         # 3 seconds between shots
    DEATH_DURATION = FPS            # 1 second death flicker

    def __init__(self, x: int, y: int):
        super().__init__(x, y, EntityType.SPIDER)
        self.pos = [float(x), float(y)]

        # Spawn point — spider returns here after chasing
        self.spawn_x = float(x)
        self.spawn_y = float(y)

        self.state = SpiderState.HANGING

        self.fire_timer  = self.FIRE_COOLDOWN  # start ready to fire
        self.death_timer = 0
        self.collected   = False
        self.distracted  = False  # True while decoy is active

        # Reference to active web — only one web per spider at a time
        self.active_web  = None

        self.animations = {
            SpiderState.HANGING: Animator(frames=[TileType.SPIDER.value], speed=20),
            SpiderState.AIMING:  Animator(frames=[TileType.SPIDER.value], speed=10),
            SpiderState.CHASING: Animator(frames=[TileType.SPIDER.value], speed=6),
            SpiderState.DEAD:    Animator(frames=[TileType.SPIDER.value], speed=4),
        }
    def _distance_to_player(self, player_rect: pygame.Rect) -> float:
        dx = (self.pos[0] + TILE_SIZE // 2) - player_rect.centerx
        dy = (self.pos[1] + TILE_SIZE // 2) - player_rect.centery
        return (dx**2 + dy**2) ** 0.5

    def update(self, player_rect: pygame.Rect) -> 'SpiderWeb | None':
        """
        Returns a SpiderWeb if one was just fired, None otherwise.
        level.py adds it to entities when returned.
        """
        new_web = None

        match self.state:
            case SpiderState.DEAD:
                self.death_timer -= 1
                if self.death_timer <= 0:
                    self.collected = True
                self.animations[self.state].update()
                return None

            case SpiderState.HANGING:
                distance = self._distance_to_player(player_rect)
                if distance < self.DETECT_RADIUS:
                    self.state = SpiderState.AIMING
                    self.fire_timer = self.FIRE_COOLDOWN  # reset timer on entry

            case SpiderState.AIMING:
                distance = self._distance_to_player(player_rect)
                if distance > self.DETECT_RADIUS:
                    # Player left range — go back to hanging
                    self.state = SpiderState.HANGING
                else:
                    # Count down fire timer
                    self.fire_timer -= 1
                    if self.fire_timer <= 0:
                        self.fire_timer = self.FIRE_COOLDOWN
                        # Fire web toward player
                        new_web = SpiderWeb(
                            int(self.pos[0]),
                            int(self.pos[1]),
                            player_rect,
                            self  # pass spider reference so web can trigger chase
                        )
                        self.active_web = new_web

            case SpiderState.CHASING:
                # Check if active web was cleared
                if self.active_web is None or self.active_web.collected:
                    # Web cleared — climb back to spawn
                    self._return_to_ceiling()
                else:
                    self._chase(player_rect)

        self.animations[self.state].update()
        return new_web

    def _chase(self, player_rect: pygame.Rect):
        dx = player_rect.centerx - (self.pos[0] + TILE_SIZE // 2)
        dy = player_rect.centery - (self.pos[1] + TILE_SIZE // 2)
        distance = (dx**2 + dy**2) ** 0.5
        if distance > 0:
            self.pos[0] += (dx / distance) * self.CHASE_SPEED
            self.pos[1] += (dy / distance) * self.CHASE_SPEED
        self.x = int(self.pos[0])
        self.y = int(self.pos[1])

    def _return_to_ceiling(self):
        """Float back up toward spawn position"""
        dx = self.spawn_x - self.pos[0]
        dy = self.spawn_y - self.pos[1]
        distance = (dx**2 + dy**2) ** 0.5
        if distance < TILE_SIZE:
            # Back at spawn — resume hanging
            self.pos = [self.spawn_x, self.spawn_y]
            self.x = int(self.pos[0])
            self.y = int(self.pos[1])
            self.state = SpiderState.HANGING
            self.active_web = None
        else:
            self.pos[0] += (dx / distance) * self.CHASE_SPEED
            self.pos[1] += (dy / distance) * self.CHASE_SPEED
            self.x = int(self.pos[0])
            self.y = int(self.pos[1])

    def hit(self):
        """Called when Guardian projectile hits the spider"""
        if self.active_web is not None:
            self.active_web.collected = True
            self.active_web = None
        self.state = SpiderState.DEAD
        self.death_timer = self.DEATH_DURATION

    def draw(self, surface: pygame.Surface, camera: Camera):
        if self.collected:
            return
        camera_pos = camera.get_pos()
        frame = self.animations[self.state].get_frame()

        # Flicker during death
        if self.state == SpiderState.DEAD:
            if self.death_timer % 4 < 2:
                return

        if self.distracted:
            frame = Tileset.change_letter_color(frame, (130, 130, 130))

        surface.blit(frame, (
            self.pos[0] - camera_pos[0],
            self.pos[1] - camera_pos[1]
        ))
    
class SpiderWeb(Entity):
    """Projectile fired by spider toward player"""
    SPEED = 2.0

    def __init__(self, x: int, y: int, player_rect: pygame.Rect, spider: Spider):
        super().__init__(x, y, EntityType.SPIDER_WEB)
        self.pos = [float(x), float(y)]
        self.collected = False
        self.spider = spider  # reference to trigger chase state

        # Calculate direction toward player at time of firing
        dx = player_rect.centerx - (x + TILE_SIZE // 2)
        dy = player_rect.centery - (y + TILE_SIZE // 2)
        distance = (dx**2 + dy**2) ** 0.5
        if distance > 0:
            self.vel_x = (dx / distance) * self.SPEED
            self.vel_y = (dy / distance) * self.SPEED
        else:
            self.vel_x = 0
            self.vel_y = self.SPEED

        self.animator = Animator(frames=[TileType.COIN.value], speed=8)

    def update(self, player_rect: pygame.Rect) -> 'WebZone | None':
        """Returns a WebZone if it hit the player, None otherwise"""
        if self.collected:
            return None

        self.pos[0] += self.vel_x
        self.pos[1] += self.vel_y
        self.x = int(self.pos[0])
        self.y = int(self.pos[1])
        self.animator.update()

        # Check hit with player
        if self.rect.colliderect(player_rect):
            web_zone = WebZone(player_rect.x, player_rect.y)
            self.spider.active_web = web_zone  # swap to zone so spider tracks its lifetime
            self.spider.state = SpiderState.CHASING
            self.collected = True
            return web_zone

        return None

    def draw(self, surface: pygame.Surface, camera: Camera):
        if self.collected:
            return
        camera_pos = camera.get_pos()
        frame = self.animator.get_frame()
        surface.blit(frame, (
            self.pos[0] - camera_pos[0],
            self.pos[1] - camera_pos[1]
        ))


class WebZone(Entity):
    """
    Stationary zone spawned where web hit the player.
    Slows movement and disables jumping while player is inside.
    Destroyed by Guardian projectile or when player exits.
    """
    def __init__(self, x: int, y: int):
        super().__init__(x, y, EntityType.WEB_ZONE)
        self.pos = [float(x), float(y)]
        self.collected = False
        self.player_inside = False
        self.animator = Animator(frames=[TileType.SPIDER_WEB.value], speed=20)

    def update(self, player_rect: pygame.Rect):
        self.player_inside = self.rect.colliderect(player_rect)
        # Disappears when player exits
        if not self.player_inside:
            self.collected = True
        self.animator.update()

    def draw(self, surface: pygame.Surface, camera: Camera):
        if self.collected:
            return
        camera_pos = camera.get_pos()
        frame = self.animator.get_frame()
        surface.blit(frame, (
            self.pos[0] - camera_pos[0],
            self.pos[1] - camera_pos[1]
        ))