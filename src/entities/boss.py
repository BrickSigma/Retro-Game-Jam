import pygame
import math
import src.tileset as Tileset
from src.tileset import TileType, TILE_SIZE
from src.camera import Camera
from src.entities.entity import Entity, EntityType
from src.animator import Animator
from src.constants import FPS
from enum import Enum, auto, unique

BOSS_SIZE    = TILE_SIZE * 4   # 32x32 visual sprite
BOSS_HITBOX  = TILE_SIZE * 2   # 16x16 collision rect, centered on sprite
PROJ_HITBOX  = TILE_SIZE // 2  # 4x4 collision rect — smaller than the 8x8 visual


@unique
class BossPhase(Enum):
    ONE   = auto()
    TWO   = auto()
    THREE = auto()
    DEAD  = auto()


@unique
class BossState(Enum):
    DORMANT       = auto()  # invisible, waiting for player to enter arena
    SPAWNING      = auto()  # growing in with flash before fight starts
    FIRING        = auto()  # firing slow projectiles at player
    WARNING       = auto()  # yellow flash — dash is incoming
    DASHING       = auto()  # fast charge to locked player position
    RESTING       = auto()  # brief pause after landing (safe to hit)
    SHAPESHIFTING = auto()  # Phase 2 entry animation
    SPLITTING     = auto()  # Phase 3 entry animation
    DYING         = auto()  # death animation


class BossProjectile(Entity):
    """Slow, aimed projectile — telegraphed enough to dodge by moving sideways."""
    COLOR = (180, 0, 0)

    def __init__(self, x: int, y: int, player_rect: pygame.Rect, speed: float = 1.2):
        super().__init__(x, y, EntityType.BOSS_PROJECTILE)
        self.pos = [float(x), float(y)]
        self.collected = False
        self.reflected = False

        dx = player_rect.centerx - (x + TILE_SIZE // 2)
        dy = player_rect.centery - (y + TILE_SIZE // 2)
        dist = (dx**2 + dy**2) ** 0.5
        if dist > 0:
            self.vel_x = (dx / dist) * speed
            self.vel_y = (dy / dist) * speed
        else:
            self.vel_x = 0
            self.vel_y = speed

        self.animator = Animator(frames=[TileType.COIN.value], speed=6)

    @property
    def rect(self):
        offset = (TILE_SIZE - PROJ_HITBOX) // 2
        return pygame.Rect(
            int(self.pos[0]) + offset,
            int(self.pos[1]) + offset,
            PROJ_HITBOX,
            PROJ_HITBOX
        )

    def reflect(self):
        """Sword hit — reverse direction and boost speed."""
        self.vel_x = -self.vel_x * 2
        self.vel_y = -self.vel_y * 2
        self.reflected = True

    def update(self, player_rect: pygame.Rect):
        if self.collected:
            return
        self.pos[0] += self.vel_x
        self.pos[1] += self.vel_y
        self.x = int(self.pos[0])
        self.y = int(self.pos[1])
        self.animator.update()

    def draw(self, surface: pygame.Surface, camera: Camera):
        if self.collected:
            return
        camera_pos = camera.get_pos()
        frame = self.animator.get_frame()
        color = (255, 220, 0) if self.reflected else self.COLOR
        frame = Tileset.change_letter_color(frame, color)
        surface.blit(frame, (
            self.pos[0] - camera_pos[0],
            self.pos[1] - camera_pos[1]
        ))


class BossCopy(Entity):
    """Fake copy spawned in Phase 3 — drifts aimlessly, never shoots."""
    DRIFT_SPEED = 0.3

    def __init__(self, x: int, y: int):
        super().__init__(x, y, EntityType.BOSS)
        self.pos = [float(x), float(y)]
        self.collected = False
        self._drift_angle = 0.0
        self.animator = Animator(frames=[TileType.FIRE.value], speed=20)

    def update(self, player_rect: pygame.Rect):
        self._drift_angle += 0.02
        self.pos[0] += math.cos(self._drift_angle) * self.DRIFT_SPEED
        self.pos[1] += math.sin(self._drift_angle) * self.DRIFT_SPEED * 0.5
        self.x = int(self.pos[0])
        self.y = int(self.pos[1])
        self.animator.update()

    def draw(self, surface: pygame.Surface, camera: Camera):
        if self.collected:
            return
        camera_pos = camera.get_pos()
        frame = self.animator.get_frame()
        frame = pygame.transform.scale(frame, (BOSS_SIZE, BOSS_SIZE))
        frame = Tileset.change_letter_color(frame, (150, 50, 50))
        surface.blit(frame, (
            self.pos[0] - camera_pos[0],
            self.pos[1] - camera_pos[1]
        ))


class Boss(Entity):
    # ---- Phase 1: slow and readable ----
    P1_SHOTS         = 3
    P1_FIRE_INTERVAL = FPS          # 1s between each shot
    P1_WARN_DURATION = FPS          # 1s yellow flash before dash
    P1_DASH_SPEED    = 1.0
    P1_REST_DURATION = FPS          # 1s rest — open window to hit the boss
    P1_PROJ_SPEED    = 0.6

    # ---- Phase 2: faster, more shots ----
    P2_SHOTS         = 5
    P2_FIRE_INTERVAL = FPS // 2     # 0.5s between shots
    P2_WARN_DURATION = FPS // 2     # 0.5s warning
    P2_DASH_SPEED    = 1.2
    P2_REST_DURATION = FPS // 2     # 0.5s rest
    P2_PROJ_SPEED    = 0.8

    # ---- Phase 3: aggressive, barely telegraphed ----
    P3_SHOTS         = 5
    P3_FIRE_INTERVAL = FPS // 2
    P3_WARN_DURATION = FPS // 3     # ~10 frames — barely time to react
    P3_DASH_SPEED    = 1.4
    P3_REST_DURATION = 0            # no rest — immediate next burst
    P3_PROJ_SPEED    = 1.0

    DASH_ARRIVE_DIST  = 4           # pixels from target to count as arrived
    ACTIVATE_RADIUS   = 10 * TILE_SIZE  # player distance that wakes the boss
    SPAWN_DURATION    = FPS * 2     # 2s grow-in animation
    SHAPESHIFT_DURATION = FPS * 2
    DEATH_DURATION      = FPS * 3
    HIT_COOLDOWN        = FPS       # 1s invulnerability between hits

    COLOR_PHASE_1 = (180, 0,   0)
    COLOR_PHASE_2 = (120, 0, 120)
    COLOR_PHASE_3 = (0,   0, 180)
    COLOR_DYING   = (220, 220, 220)
    COLOR_WARNING = (255, 220,  0)  # bright yellow — "incoming dash!"

    def __init__(self, x: int, y: int):
        super().__init__(x, y, EntityType.BOSS)

        self.rect = pygame.Rect(x, y, BOSS_SIZE, BOSS_SIZE)
        self.pos  = [float(x), float(y)]

        self.spawn_x = float(x)
        self.spawn_y = float(y)

        self.phase     = BossPhase.ONE
        self.state     = BossState.DORMANT
        self.hits      = 0
        self.collected = False
        self.direction = 1

        self._spawn_timer = 0

        # Fire-warn-dash-rest cycle
        self.fire_timer    = self.P1_FIRE_INTERVAL
        self.shots_fired   = 0
        self.warning_timer = 0
        self.dash_target   = [0.0, 0.0]
        self._dash_speed   = 0.0
        self.rest_timer    = 0

        # Phase transition
        self.death_timer      = 0
        self.shapeshift_timer = 0
        self.split_done       = False
        self.ghosts_summoned  = False

        self._hit_cooldown   = 0
        self._death_flicker  = 0

        self.copies: list[BossCopy] = []

        self._pending_projectiles: list[BossProjectile] = []
        self._pending_ghosts: int = 0
        self._pending_copies: list[BossCopy] = []

        self.animator = Animator(frames=[TileType.FIRE.value], speed=15)

    @property
    def rect(self):
        offset = (BOSS_SIZE - BOSS_HITBOX) // 2
        return pygame.Rect(int(self.pos[0]) + offset, int(self.pos[1]) + offset, BOSS_HITBOX, BOSS_HITBOX)

    @rect.setter
    def rect(self, value):
        self.pos = [float(value.x), float(value.y)]

    @property
    def distracted(self) -> bool:
        """Reuses the distracted flag player.py already checks — no contact damage while dormant/spawning."""
        return self.state in (BossState.DORMANT, BossState.SPAWNING)

    def _phase_color(self) -> tuple:
        match self.phase:
            case BossPhase.ONE:   return self.COLOR_PHASE_1
            case BossPhase.TWO:   return self.COLOR_PHASE_2
            case BossPhase.THREE: return self.COLOR_PHASE_3
            case _:               return self.COLOR_DYING

    def _phase_params(self) -> dict:
        match self.phase:
            case BossPhase.ONE:
                return dict(shots=self.P1_SHOTS, fire_interval=self.P1_FIRE_INTERVAL,
                            warn=self.P1_WARN_DURATION, dash=self.P1_DASH_SPEED,
                            rest=self.P1_REST_DURATION, proj_speed=self.P1_PROJ_SPEED)
            case BossPhase.TWO:
                return dict(shots=self.P2_SHOTS, fire_interval=self.P2_FIRE_INTERVAL,
                            warn=self.P2_WARN_DURATION, dash=self.P2_DASH_SPEED,
                            rest=self.P2_REST_DURATION, proj_speed=self.P2_PROJ_SPEED)
            case _:
                return dict(shots=self.P3_SHOTS, fire_interval=self.P3_FIRE_INTERVAL,
                            warn=self.P3_WARN_DURATION, dash=self.P3_DASH_SPEED,
                            rest=self.P3_REST_DURATION, proj_speed=self.P3_PROJ_SPEED)

    def _distance_to_player(self, player_rect: pygame.Rect) -> float:
        dx = (self.pos[0] + BOSS_SIZE // 2) - player_rect.centerx
        dy = (self.pos[1] + BOSS_SIZE // 2) - player_rect.centery
        return (dx**2 + dy**2) ** 0.5

    def _reset_fire_cycle(self):
        """Start a fresh firing burst using the current phase's parameters."""
        params = self._phase_params()
        self.fire_timer  = params['fire_interval']
        self.shots_fired = 0
        self.state       = BossState.FIRING

    def hit(self) -> bool:
        if self.state in (BossState.DORMANT, BossState.SPAWNING):
            return False
        if self._hit_cooldown > 0:
            return False
        self._hit_cooldown = self.HIT_COOLDOWN
        self.hits += 1

        if self.hits >= 6:
            self.pos[0] = self.spawn_x
            self.pos[1] = self.spawn_y
            self.phase          = BossPhase.DEAD
            self.state          = BossState.DYING
            self.death_timer    = self.DEATH_DURATION
            self._death_flicker = 0
            return True

        if self.hits == 2:
            self.phase = BossPhase.TWO
            self.state = BossState.SHAPESHIFTING
            self.shapeshift_timer = self.SHAPESHIFT_DURATION
            self.ghosts_summoned = False
        elif self.hits == 4:
            self.phase = BossPhase.THREE
            self.state = BossState.SPLITTING
            self.split_done = False
            self.copies = []

        return False

    def snap_to_copy(self, copy: 'BossCopy'):
        """Player touched a copy — boss rushes to it, then resumes attacking."""
        self.dash_target = [copy.pos[0], copy.pos[1]]
        self._dash_speed = 2.0  # noticeably faster than any normal dash
        copy.collected = True
        self.copies = [c for c in self.copies if not c.collected]
        self.state = BossState.DASHING

    def update(self, player_rect: pygame.Rect) -> dict:
        result = {'projectiles': [], 'ghosts': 0, 'copies': [], 'defeated': False}

        if self._hit_cooldown > 0:
            self._hit_cooldown -= 1

        # --- DORMANT ---
        if self.state == BossState.DORMANT:
            if self._distance_to_player(player_rect) <= self.ACTIVATE_RADIUS:
                self.state = BossState.SPAWNING
                self._spawn_timer = self.SPAWN_DURATION
            self.animator.update()
            return result

        # --- SPAWNING ---
        if self.state == BossState.SPAWNING:
            self._spawn_timer -= 1
            if self._spawn_timer <= 0:
                self._reset_fire_cycle()
            self.animator.update()
            return result

        # --- DYING ---
        if self.state == BossState.DYING:
            self._death_flicker += 1
            self.death_timer -= 1
            if self.death_timer <= 0:
                self.collected = True
                result['defeated'] = True
            self.animator.update()
            return result

        params = self._phase_params()

        # --- SHAPESHIFTING (Phase 2 entry) ---
        if self.state == BossState.SHAPESHIFTING:
            self.shapeshift_timer -= 1
            if not self.ghosts_summoned and self.shapeshift_timer < self.SHAPESHIFT_DURATION // 2:
                self.ghosts_summoned = True
                result['ghosts'] = 2
            if self.shapeshift_timer <= 0:
                self._reset_fire_cycle()
            self.animator.update()
            return result

        # --- SPLITTING (Phase 3 entry) ---
        if self.state == BossState.SPLITTING and not self.split_done:
            copy1 = BossCopy(int(self.pos[0]) - BOSS_SIZE * 2, int(self.pos[1]))
            copy2 = BossCopy(int(self.pos[0]) + BOSS_SIZE * 2, int(self.pos[1]))
            self.copies = [copy1, copy2]
            result['copies'] = [copy1, copy2]
            self.split_done = True
            self._reset_fire_cycle()
            self.animator.update()
            return result

        # --- FIRING ---
        if self.state == BossState.FIRING:
            self.fire_timer -= 1
            if self.fire_timer <= 0:
                result['projectiles'].append(BossProjectile(
                    int(self.pos[0] + BOSS_SIZE // 2),
                    int(self.pos[1] + BOSS_SIZE // 2),
                    player_rect,
                    speed=params['proj_speed']
                ))
                self.shots_fired += 1
                if self.shots_fired >= params['shots']:
                    self.state = BossState.WARNING
                    self.warning_timer = params['warn']
                    self.shots_fired = 0
                else:
                    self.fire_timer = params['fire_interval']

        # --- WARNING ---
        elif self.state == BossState.WARNING:
            self.warning_timer -= 1
            dx = player_rect.centerx - (self.pos[0] + BOSS_SIZE // 2)
            self.direction = 1 if dx > 0 else -1
            if self.warning_timer <= 0:
                # Lock target to player's position RIGHT NOW
                self.dash_target = [
                    float(player_rect.centerx - BOSS_SIZE // 2),
                    float(player_rect.centery - BOSS_SIZE // 2),
                ]
                self._dash_speed = params['dash']
                self.state = BossState.DASHING

        # --- DASHING ---
        elif self.state == BossState.DASHING:
            dx = self.dash_target[0] - self.pos[0]
            dy = self.dash_target[1] - self.pos[1]
            dist = (dx**2 + dy**2) ** 0.5
            if dist < self.DASH_ARRIVE_DIST:
                if params['rest'] > 0:
                    self.state = BossState.RESTING
                    self.rest_timer = params['rest']
                else:
                    self._reset_fire_cycle()
            else:
                self.pos[0] += (dx / dist) * self._dash_speed
                self.pos[1] += (dy / dist) * self._dash_speed
                self.direction = 1 if dx > 0 else -1

        # --- RESTING ---
        elif self.state == BossState.RESTING:
            self.rest_timer -= 1
            if self.rest_timer <= 0:
                self._reset_fire_cycle()

        if self.phase == BossPhase.THREE:
            for copy in self.copies:
                copy.update(player_rect)

        self.animator.update()
        return result

    def draw(self, surface: pygame.Surface, camera: Camera):
        if self.collected:
            return
        if self.state == BossState.DORMANT:
            return

        camera_pos = camera.get_pos()
        frame = self.animator.get_frame()

        if self.state == BossState.SPAWNING:
            progress = 1.0 - (self._spawn_timer / self.SPAWN_DURATION)
            size = max(TILE_SIZE, int(BOSS_SIZE * progress))
            frame = pygame.transform.scale(frame, (size, size))
            if self._spawn_timer % 6 < 3:
                frame = Tileset.change_letter_color(frame, (255, 255, 255))
            else:
                frame = Tileset.change_letter_color(frame, self._phase_color())
            offset = (BOSS_SIZE - size) // 2
            surface.blit(frame, (
                self.pos[0] - camera_pos[0] + offset,
                self.pos[1] - camera_pos[1] + offset
            ))
            return

        frame = pygame.transform.scale(frame, (BOSS_SIZE, BOSS_SIZE))

        if self.phase == BossPhase.DEAD:
            if self._death_flicker % 6 < 3:
                frame = Tileset.change_letter_color(frame, self.COLOR_DYING)
            else:
                return
        elif self.state == BossState.WARNING:
            # Alternate yellow ↔ phase color — clear visual cue for the incoming dash
            if self.warning_timer % 8 < 4:
                frame = Tileset.change_letter_color(frame, self.COLOR_WARNING)
            else:
                frame = Tileset.change_letter_color(frame, self._phase_color())
        elif self.state == BossState.SHAPESHIFTING:
            # Rapid flicker white ↔ new phase color during transition
            if self.shapeshift_timer % 8 < 4:
                frame = Tileset.change_letter_color(frame, (255, 255, 255))
            else:
                frame = Tileset.change_letter_color(frame, self._phase_color())
        else:
            frame = Tileset.change_letter_color(frame, self._phase_color())

        surface.blit(frame, (
            self.pos[0] - camera_pos[0],
            self.pos[1] - camera_pos[1]
        ))

        if self.phase == BossPhase.THREE:
            for copy in self.copies:
                copy.draw(surface, camera)
