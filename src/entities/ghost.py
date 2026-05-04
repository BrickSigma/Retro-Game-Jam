from enum import Enum, auto, unique
import pygame
import src.tileset as Tileset
from src.tileset import TileType, TILE_SIZE
from src.camera import Camera
from src.entities.entity import Entity, EntityType
from src.animator import Animator

@unique
class GhostState(Enum):
    PATROLLING = auto() # floating left/right, ignoring player
    AGITATED = auto() # player detected, moving towards them faster
    ATTACKING = auto() # close enough, firing projectile

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

    def __init__(self, x:int , y:int):
        super().__init__(x,y, EntityType.GHOST)

        # Float positions for sub-pixel movement
        self.pos = [float(x), float(y)]

        # spawn point
        self.spawn_x = x
        self.spawn_y = y

        self.direction = 1

        self.state = GhostState.PATROLLING

        # Animator
        self.animatons = {
            GhostState.PATROLLING: Animator(frames=[TileType.GHOST.value], speed=20),
            GhostState.AGITATED:   Animator(frames=[TileType.GHOST.value], speed=10),
            GhostState.ATTACKING:  Animator(frames=[TileType.GHOST.value], speed=5),
        }
    def _distance_to_player(self, player_rect: pygame.Rect) -> float:
        """Calculate pixel distance between ghost center and player center"""
        dx = (self.pos[0] + TILE_SIZE // 2) - player_rect.centerx
        dy = (self.pos[1] + TILE_SIZE // 2) - player_rect.centery
        return (dx**2 + dy**2) ** 0.5 # Pythagoras Oh ive missed you!
    
    def update(self, player_rect: pygame.Rect):
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
        self.animatons[self.state].update()
    
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

    def draw(self, surface:pygame.Surface, camera:Camera):
        camera_pos = camera.get_pos()
        frame = self.animatons[self.state].get_frame()

        # Flip sprite based on direction so ghost faces the player
        if self.direction == -1:
            frame = pygame.transform.flip(frame, True, False)
        
        surface.blit(frame,(
            self.pos[0] - camera_pos[0],
            self.pos[1] - camera_pos[1]
        ))



