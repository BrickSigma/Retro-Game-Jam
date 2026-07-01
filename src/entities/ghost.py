from enum import Enum, auto, unique
import pygame
import src.tileset as Tileset
from src.tileset import TileType, TILE_SIZE
from src.camera import Camera
from src.entities.entity import Entity, EntityType
from src.animator import Animator
from src.constants import FPS

@unique
class GhostState(Enum):
    PATROLLING = auto() # floating left/right, ignoring player
    AGITATED = auto() # player detected, moving towards them faster
    ATTACKING = auto() # close enough, firing projectile
    STUNNED = auto() # when ghost is hit by projectile
    DYING = auto()

class Ghost(Entity):
    # Movement speeds
    PATROL_SPEED = 0.3
    CHASE_SPEED = 0.6
    ATTACK_SPEED = 0.9

    # Detection radii in pixels
    DETECT_RADIUS = 6 * TILE_SIZE
    ATTACK_RADIUS = 3 * TILE_SIZE

    # How far left/right from spawn the ghost patrols
    PATROL_RANGE = 4 * TILE_SIZE

    STUN_DURATION = FPS * 2

    def __init__(self, x:int , y:int):
        super().__init__(x,y, EntityType.GHOST)

        # Float positions for sub-pixel movement
        self.pos = [float(x), float(y)]

        # spawn point
        self.spawn_x = x
        self.spawn_y = y

        self.direction = 1

        self.state = GhostState.PATROLLING

        self.hits = 0
        self.stun_timer = 0
        self.death_timer = 0
        self.collected = False  # True when hit twice, removed by level.py
        self.distracted = False  # True while decoy is active

        # Animator
        self.animations = {
            GhostState.PATROLLING: Animator(frames=[TileType.GHOST.value], speed=20),
            GhostState.AGITATED:   Animator(frames=[TileType.GHOST.value], speed=10),
            GhostState.ATTACKING:  Animator(frames=[TileType.GHOST.value], speed=5),
            GhostState.STUNNED: Animator(frames=[TileType.GHOST.value], speed=30),
            GhostState.DYING: Animator(frames=[TileType.GHOST.value], speed=4)
        }
    def _distance_to_player(self, player_rect: pygame.Rect) -> float:
        """Calculate pixel distance between ghost center and player center"""
        dx = (self.pos[0] + TILE_SIZE // 2) - player_rect.centerx
        dy = (self.pos[1] + TILE_SIZE // 2) - player_rect.centery
        return (dx**2 + dy**2) ** 0.5 # Pythagoras Oh ive missed you!
    
    def update(self, player_rect: pygame.Rect):
         # Handle dying state
        if self.state == GhostState.DYING:
            self.death_timer -= 1
            if self.death_timer <= 0:
                self.collected = True  # now actually remove it
            self.animations[self.state].update()
            return  # skip all movement while dying
    
        # Handle stun countdown
        if self.state == GhostState.STUNNED:
            self.stun_timer -= 1
            if self.stun_timer <= 0:
                self.state = GhostState.PATROLLING  # resume after stun
            self.animations[self.state].update()
            return  # skip all movement while stunned
        
        distance = self._distance_to_player(player_rect)

        # State transitions
        match self.state:
            case GhostState.PATROLLING:
                if distance < self.DETECT_RADIUS:
                    self.state = GhostState.AGITATED

            case GhostState.AGITATED:
                if distance > self.DETECT_RADIUS:
                    # if player escaped go backto patrolling
                    self.state = GhostState.PATROLLING
                elif distance < self.ATTACK_RADIUS:
                    self.state = GhostState.ATTACKING
            
            case GhostState.ATTACKING:
                if distance > self.ATTACK_RADIUS:
                    # player backed away - return to agitated
                    self.state = GhostState.AGITATED
        
        match self.state:
            case GhostState.PATROLLING:
                self._patrol()
            case GhostState.AGITATED | GhostState.ATTACKING:
                self._chase(player_rect)
        
        # Tick the animator
        self.animations[self.state].update()


    
    def _patrol(self):
        """
        Float left and right within PATROL_RANGE of spawn point.
        Turns around when it hits the boundary.
        """
        self.pos[0] += self.PATROL_SPEED * self.direction

        # Check if ghost has reached patrol boundary and flip direction
        if self.pos[0] > self.spawn_x + self.PATROL_RANGE:
            self.direction = -1
        elif self.pos[0] < self.spawn_x - self.PATROL_RANGE:
            self.direction = 1
        self.x = int(self.pos[0])
        self.y = int(self.pos[1])
    
    def _chase(self, player_rect: pygame.Rect):
        """
        Move toward the player at chase speed.
        Updates direction so the sprite faces the right way.
        """ 
        dx = player_rect.centerx - (self.pos[0] + TILE_SIZE // 2)
        dy = player_rect.centery - (self.pos[1] + TILE_SIZE // 2)

        # Normalise the direction vector so diagonal movement
        # isnt faster than horizontal/vertial 
        distance = (dx**2 + dy**2) ** 0.5
        if distance > 0:
            match self.state:
                case GhostState.AGITATED:
                    speed = self.CHASE_SPEED
                case GhostState.ATTACKING:
                    speed = self.ATTACK_SPEED
                case _:
                    speed = self.PATROL_SPEED
            self.pos[0] += (dx / distance) * speed
            self.pos[1] += (dy / distance) * speed
        
        # Update facing direction for sprite flip in draw()
        self.direction = 1 if dx > 0 else -1
        # Sync rect to float position
        self.x = int(self.pos[0])
        self.y = int(self.pos[1])

    def draw(self, surface: pygame.Surface, camera: Camera):
        if self.collected:
            return

        camera_pos = camera.get_pos()
        frame = self.animations[self.state].get_frame()

        match self.state:
            case GhostState.STUNNED:
                # Alternate between grey and normal every 8 frames
                if (self.stun_timer // 8) % 2 == 0:
                    frame = Tileset.change_letter_color(frame, (100, 100, 255))  # blue tint when stunned
                
            case GhostState.DYING:
                # Rapid flicker before disappearing
                if self.death_timer % 4 < 2:
                    return  # skip drawing every other 2 frames

        if self.distracted:
            frame = Tileset.change_letter_color(frame, (130, 130, 130))

        if self.direction == -1:
            frame = pygame.transform.flip(frame, True, False)

        surface.blit(frame, (
            self.pos[0] - camera_pos[0],
            self.pos[1] - camera_pos[1]
        ))

    def hit(self):
        """Called when a projectile hits the ghost"""
        if self.state == GhostState.DYING or self.collected:
            return  # already dying — don't reset death_timer or double-count hits
        self.hits += 1
        if self.hits >= 2:
            self.state = GhostState.DYING  # play death effect first
            self.death_timer = FPS  # 1 second death animation
        else:
            self.state = GhostState.STUNNED
            self.stun_timer = self.STUN_DURATION



