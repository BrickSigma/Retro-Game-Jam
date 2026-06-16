"""
Level module for the game.

This handles the core logic of the game that puts everything
from the player, tiles, enemies, and so on, all together into one scene.

Most of the gameplay takes place here.
"""
from enum import Enum, unique, auto
import pygame

from src.entities.torch import Torch
import src.tileset as Tileset
from src.tileset import TileType
from src.constants import resource_path, FPS
from src.camera import Camera, CameraState
from src.tiledmap import TiledMap
from src.player import Player, PlayerUpdateState, PlayerState
from src.entities import *
from src.guardian import Guardian, GuardianState
import src.gamepad as Gamepad

"""
INTERNAL NOTES:
Each level has the following components:
    1. Background layer with non-interactable tiles
    2. Tile/platform layer used for walking on
    3. Items/collectables/enemies/other entities layer
    4. The player camera
"""

@unique
class LevelState(Enum):
    NO_CHANGE = auto()
    NEXT_LEVEL = auto()     # Moves onto the next level
    GAME_OVER = auto()
    QUIT = auto()
    BOSS_DEFEATED = auto()  # boss killed — triggers credits

@unique
class MapTiles(Enum):
    NONE = 0
    BLOCK = 1
    RAMP_LEFT = 2
    RAMP_RIGHT = 3

class Level:
    PALETTE = {
        'green':  (120, 131, 116),
        'cream':  (245, 233, 191),
        'red':    (170, 100, 77),
        'purple': (55, 42, 57),
        'background': (32, 34, 54)
    }

    LAYER_PLATFORM_GREEN  = "platform_green"
    LAYER_PLATFORM_CREAM  = "platform_cream"
    LAYER_PLATFORM_RED    = "platform_red"
    LAYER_PLATFORM_PURPLE = "platform_purple"

    LAYER_BG_GREEN  = "background_green"
    LAYER_BG_CREAM  = "background_cream"
    LAYER_BG_RED    = "background_red"
    LAYER_BG_PURPLE = "background_purple"

    LAYER_ITEMS = "items"

    # Legacy layer names — kept for levels not yet migrated to palette naming
    LAYER_PLATFORM   = "platform"
    LAYER_BACKGROUND = "background"
    LAYER_BACKGROUND2 = "background2"

    def __init__(self, 
                 surface: pygame.Surface, 
                 level_no: int, 
                 camera_type: CameraState = CameraState.HORIZONTAL, 
                 hud_background: tuple[float] = (47, 36, 59),
                 background_layer: bool = True):
        
        self.surface = surface
        self.level_no = level_no
        self.level_folder = resource_path(f"assets/levels/{self.level_no}")

        self.hud_background = hud_background
        self.background_layer: pygame.Surface | None = None

        if background_layer:
            self.background_layer = pygame.image.load(resource_path(f"{self.level_folder}/background.png"))

        """
        Every item in the game is dependant on the player's position,
        as it determines the camera viewport and scroll.
        """

        # Load the entire platform surface from a PNG
        self.platform_surface = pygame.image.load(f"{self.level_folder}/platform.png")
        self.platform_surface.convert_alpha()
        self.platform_surface.set_colorkey(self.PALETTE['background'])

        self.tilemap = TiledMap(f"{self.level_folder}/level.tmx")
        self.entities = self.tilemap.get_entities()
        self.player_start: Entity = None
        player_index = -1
        for i, entity in enumerate(self.entities):
            if entity.type == EntityType.PLAYER:
                player_index = i
                self.player_start = entity
                break
        self.entities.pop(player_index)

        # Create player at spawn, then attach guardian
        self.player = Player((self.player_start.x, self.player_start.y), self.tilemap.size())
        self.guardian = Guardian(self.player, pos=(self.player_start.x, self.player_start.y))

        self.camera = Camera((self.player.pos[0], self.player.pos[1]), camera_type, self.tilemap.size())
        self.viewport = pygame.Surface((32 * 8, 27 * 8))

        # Lives system - 3 is the starting amount
        self.MAX_LIVES = 3
        self.lives = self.MAX_LIVES

        # Spirit charges
        self.MAX_CHARGES = 3
        self.charges = self.MAX_CHARGES

        self.boss_defeated   = False
        self.arena_locked    = False
        self._credits_timer  = 0
        self._checkpoint_data: dict | None = None

        # HUD banners — built once, not every frame
        self.level_banner = Tileset.render_string(f"Level: {level_no}")
        self.lives_banner = Tileset.render_string(f"Lives: {self.lives}")
        
        # restart() called last — player and guardian are ready
        self.restart()
        

    def restart(self):
        """
        Restart the level.
        This basically sets up the initial state of the level, so things like
        the player position, camera position and state, and any entities are loaded.
        """
        self.lives = self.MAX_LIVES
        self.charges = self.MAX_CHARGES
        self.boss_defeated   = False
        self.arena_locked    = False
        self._credits_timer  = 0
        self._checkpoint_data = None  # full restart clears checkpoint
        self.camera.unlock()
        self.lives_banner = Tileset.render_string(f"Lives: {self.lives}")

        # Reset all guardian upgrades on full restart
        self.guardian.upgraded_l2    = False
        self.guardian.upgraded_l3    = False
        self.guardian.can_shield     = False
        self.guardian.can_bounce_pad = False
        self.guardian.can_use_sword  = False
        self.guardian.can_use_decoy  = False
        self.guardian.shield_active  = False
        self.guardian.flash_timer    = 0

        self.entities = self.tilemap.get_entities()
        self.entities = [e for e in self.entities if e.type != EntityType.PLAYER]
        self._respawn_player()

    def respawn(self):
        """
        Soft reset — called when the player dies but still has lives remaining.
        If a checkpoint was hit, player respawns there with guardian state restored.
        """
        self.charges        = self.MAX_CHARGES
        self.boss_defeated  = False
        self.arena_locked   = False
        self._credits_timer = 0
        self.camera.unlock()
        self.entities = self.tilemap.get_entities()
        self.entities = [e for e in self.entities if e.type != EntityType.PLAYER]

        if self._checkpoint_data:
            self._respawn_at_checkpoint()
            # Re-activate the checkpoint entity so it stays gold after respawn
            for entity in self.entities:
                if (isinstance(entity, Checkpoint)
                        and entity.x == self._checkpoint_data['x']
                        and entity.y == self._checkpoint_data['y']):
                    entity.activated = True
                    break
        else:
            self._respawn_player()

    def _get_all_platform_tiles(self, tiles_rect: pygame.Rect):
        platform_layers = [
            self.LAYER_PLATFORM,
            self.LAYER_PLATFORM_GREEN,
            self.LAYER_PLATFORM_CREAM,
            self.LAYER_PLATFORM_RED,
            self.LAYER_PLATFORM_PURPLE,
        ]

        combined = self.tilemap.get_tiles_rect(tiles_rect, platform_layers[0])

        if combined is None:
            from src.tile import Tile, TileType as TT
            combined = [
                [Tile(tiles_rect.x + x, tiles_rect.y + y, TT.NONE, False, False)
                 for x in range(tiles_rect.w)]
                for y in range(tiles_rect.h)
            ]

        for layer_name in platform_layers[1:]:
            layer_tiles = self.tilemap.get_tiles_rect(tiles_rect, layer_name)
            if layer_tiles is None:
                continue
            for y in range(len(combined)):
                for x in range(len(combined[y])):
                    if layer_tiles[y][x].type != TileType.NONE:
                        combined[y][x] = layer_tiles[y][x]

        return combined

    def _respawn_player(self):
        """
        Shared logic between restart() and respawn().
        Moves the player back to the spawn point and clears the guardian path.
        """
        self.player.pos = [self.player_start.x, self.player_start.y]
        self.player.rect.x = self.player_start.x
        self.player.rect.y = self.player_start.y
        self.player.state = PlayerState.IDLE
        self.player.y_momentum = 0
        self.player._invulnerability_timer = 0  # clear any invulnerability on respawn

        # Reset all guardian upgrades on death
        self.guardian.upgraded_l2    = False
        self.guardian.upgraded_l3    = False
        self.guardian.can_shield     = False
        self.guardian.can_bounce_pad = False
        self.guardian.can_use_sword  = False
        self.guardian.can_use_decoy  = False
        self.guardian.shield_active  = False
        self.guardian.flash_timer    = 0
        self.guardian.state          = GuardianState.FOLLOWING

    def _save_checkpoint(self, entity: 'Checkpoint'):
        """Snapshot the current player/guardian state when a checkpoint is touched."""
        self._checkpoint_data = {
            'x': entity.x,
            'y': entity.y,
            'wielding_sword': self.player.wielding_sword,
            'guardian': {
                'upgraded_l2':    self.guardian.upgraded_l2,
                'upgraded_l3':    self.guardian.upgraded_l3,
                'can_shield':     self.guardian.can_shield,
                'can_bounce_pad': self.guardian.can_bounce_pad,
                'can_use_sword':  self.guardian.can_use_sword,
                'can_use_decoy':  self.guardian.can_use_decoy,
            }
        }

        # Also stop the music so that the boss music can start.
        pygame.mixer.music.unload()

    def _respawn_at_checkpoint(self):
        """Restore player and guardian to the saved checkpoint state."""
        cp = self._checkpoint_data
        self.player.pos    = [float(cp['x']), float(cp['y'])]
        self.player.rect.x = cp['x']
        self.player.rect.y = cp['y']
        self.player.state  = PlayerState.IDLE
        self.player.y_momentum = 0
        self.player._invulnerability_timer = 0
        self.player.wielding_sword = cp['wielding_sword']

        g = cp['guardian']
        self.guardian.upgraded_l2    = g['upgraded_l2']
        self.guardian.upgraded_l3    = g['upgraded_l3']
        self.guardian.can_shield     = g['can_shield']
        self.guardian.can_bounce_pad = g['can_bounce_pad']
        self.guardian.can_use_sword  = g['can_use_sword']
        self.guardian.can_use_decoy  = g['can_use_decoy']
        self.guardian.shield_active  = False
        self.guardian.flash_timer    = 0
        self.guardian.state          = GuardianState.FOLLOWING
        
    def handle_music(self):
        """
        Used to handle the background music for the game.
        """
        if pygame.mixer.music.get_busy():
            return  # Do nothing if it's already playing a track
        
        if self._checkpoint_data is not None:
            pygame.mixer.music.load(f"{self.level_folder}/boss.mp3")
        else:
            pygame.mixer.music.load(f"{self.level_folder}/music.wav")
            
        pygame.mixer.music.set_volume(0.2)
        pygame.mixer.music.play(fade_ms=2000)
        

    def update(self) -> LevelState:
        next_state = LevelState.NO_CHANGE

        self.handle_music()
        
        events = pygame.event.get()

        # Event handling can take place here
        for event in events:
            match event.type:
                case pygame.JOYDEVICEADDED:
                    Gamepad.init()
                case pygame.QUIT:
                    next_state = LevelState.QUIT
                case pygame.KEYDOWN:
                    match event.key:
                        case pygame.K_ESCAPE:
                            next_state = LevelState.QUIT
                        case pygame.K_BACKSPACE:
                            self.restart()
                        case pygame.K_l:
                            # Platform controls
                            if self.charges > 0:
                                player_airborne = self.player.state in (PlayerState.JUMPING, PlayerState.FALLING)
                                player_vel = [
                                    self.player.VEL if self.player.moving_right else -self.player.VEL if self.player.moving_left else 0,
                                    self.player.y_momentum
                                ]
                                spent = self.guardian.activate_platform(
                                    self.player.rect,
                                    self.player.facing_right,
                                    player_airborne,
                                    player_vel
                                )
                                if spent:
                                    self.charges -= 1
                        case pygame.K_k:
                            # Shoot projectile
                            if self.charges > 0:
                                projectile = self.guardian.fire_projectile(
                                    self.player.rect,
                                    self.player.facing_right
                                )
                                if projectile is not None:
                                    self.entities.append(projectile)
                                    self.charges -= 1
                        case pygame.K_p:
                            # Activate shield
                            if self.charges > 0 and self.guardian.can_shield:
                                spent = self.guardian.activate_shield()
                                if spent:
                                    self.charges -= 1
                        case pygame.K_o:
                            # Activate bounce pad
                            if self.charges > 0:
                                player_airborne = self.player.state in (PlayerState.JUMPING, PlayerState.FALLING)
                                player_vel = [
                                    self.player.VEL if self.player.moving_right else -self.player.VEL if self.player.moving_left else 0,
                                    self.player.y_momentum
                                ]
                                spent = self.guardian.activate_bounce_pad(
                                    self.player.rect,
                                    self.player.facing_right,
                                    player_airborne,
                                    player_vel
                                )
                                if spent:
                                    self.charges -= 1
                        case pygame.K_m:
                            # Activate sword
                            if not self.player.wielding_sword:
                                if self.charges > 0:
                                    spent = self.guardian.activate_sword()
                                    if spent:
                                        self.charges -= 1
                                        self.player.wielding_sword = True
                        case pygame.K_n:
                            if self.charges > 0:
                                spent = self.guardian.activate_decoy()
                                if spent:
                                    self.charges -= 1
                
                case pygame.JOYBUTTONDOWN:
                    match event.button:
                        case 1:  # B Button
                            # Platform controls
                            if self.charges > 0:
                                player_airborne = self.player.state in (PlayerState.JUMPING, PlayerState.FALLING)
                                player_vel = [
                                    self.player.VEL if self.player.moving_right else -self.player.VEL if self.player.moving_left else 0,
                                    self.player.y_momentum
                                ]
                                spent = self.guardian.activate_platform(
                                    self.player.rect,
                                    self.player.facing_right,
                                    player_airborne,
                                    player_vel
                                )
                                if spent:
                                    self.charges -= 1

                        case 2:  # Right bumper button
                            # Shoot projectile
                            if self.charges > 0:
                                projectile = self.guardian.fire_projectile(
                                    self.player.rect,
                                    self.player.facing_right
                                )
                                if projectile is not None:
                                    self.entities.append(projectile)
                                    self.charges -= 1

                        case 3:  # Y Button
                            # Activate bounce pad
                            if self.charges > 0:
                                player_airborne = self.player.state in (PlayerState.JUMPING, PlayerState.FALLING)
                                player_vel = [
                                    self.player.VEL if self.player.moving_right else -self.player.VEL if self.player.moving_left else 0,
                                    self.player.y_momentum
                                ]
                                spent = self.guardian.activate_bounce_pad(
                                    self.player.rect,
                                    self.player.facing_right,
                                    player_airborne,
                                    player_vel
                                )
                                if spent:
                                    self.charges -= 1

                        case 4:  # Left bumber button
                            # Activate shield
                            if self.charges > 0 and self.guardian.can_shield:
                                spent = self.guardian.activate_shield()
                                if spent:
                                    self.charges -= 1
                        
                        case 5:  # Right bumber button
                            # Activate sword
                            if not self.player.wielding_sword:
                                if self.charges > 0:
                                    spent = self.guardian.activate_sword()
                                    if spent:
                                        self.charges -= 1
                                        self.player.wielding_sword = True

                case pygame.JOYHATMOTION:
                    if event.value[1] == -1:  # D-pad down button
                        if self.charges > 0:
                            spent = self.guardian.activate_decoy()
                            if spent:
                                self.charges -= 1

        tiles_rect = pygame.Rect(
            (self.player.rect.x//Tileset.TILE_SIZE) - 1, 
            (self.player.rect.y//Tileset.TILE_SIZE) - 1, 
            4, 
            4)
        adjecent_tiles = self._get_all_platform_tiles(tiles_rect)
        # build guardian platform rect if active
        if self.guardian.state in (GuardianState.PLATFORM, GuardianState.BOUNCE_PAD):
            guardian_platform = self.guardian.rect
        else:
            guardian_platform = None

        player_state = self.player.update(
            events,
            adjecent_tiles,
            self.entities,
            guardian_platform
        )

        # Clamp player to the locked camera viewport — both edges are arena walls
        if self.camera.locked:
            left  = int(self.camera.pos[0])
            right = int(self.camera.pos[0]) + Camera.WIDTH - self.player.rect.width
            if self.player.pos[0] < left:
                self.player.pos[0] = float(left)
                self.player.rect.x = left
            elif self.player.pos[0] > right:
                self.player.pos[0] = float(right)
                self.player.rect.x = right

        match player_state:
            case PlayerUpdateState.NO_CHANGE:
                pass
            case PlayerUpdateState.DIED:
                self.lives = max(0, self.lives - 1)
                if self.lives <=0:
                    # Also stop the music
                    pygame.mixer.music.unload()
                    next_state = LevelState.GAME_OVER # signal game over to game.py
                else:
                    self.respawn() # sof reset, keep remaining lives
            case PlayerUpdateState.COMPLETED_LEVEL:
                # Stop the music as well
                pygame.mixer.music.unload()
                next_state = LevelState.NEXT_LEVEL

        # Camera: pan to boss during spawn, lock once the fight starts
        if self.arena_locked:
            boss_entity = next((e for e in self.entities if isinstance(e, Boss)), None)
            if boss_entity and boss_entity.state == BossState.SPAWNING:
                self.camera.update(boss_entity.rect)  # lerp toward boss
            elif not self.camera.locked:
                self.camera.lock()                     # fight started — freeze here
        else:
            self.camera.update(self.player.rect)

        # Clear surface
        self.surface.fill(self.hud_background)
        if self.background_layer is not None:
            self.viewport.blit(self.background_layer)
        else:
            self.viewport.fill(self.hud_background)

        # Draw HUD - level name on left, hearts on right
        Tileset.render_tile(self.surface, self.level_banner, 0, 0)
        heart = Tileset.get_tile(TileType.HEART.value)
        for i in range(self.lives):
            Tileset.render_tile(self.surface, heart, 20 + i, 0)

        # Draw spirt charge orbs next to hearts
        orb = Tileset.get_tile(TileType.JEWEL.value)
        empty_orb = Tileset.change_letter_color(orb, (80, 80, 80))
        for i in range(self.MAX_CHARGES):
            if i < self.charges:
                Tileset.render_tile(self.surface, orb, 24 + i, 0)
            else:
                Tileset.render_tile(self.surface, empty_orb, 24 + i, 0)
    
        # Draw world layers
        # Legacy layers — drawn first so palette layers render on top during migration
        # self.tilemap.draw_layer(self.viewport, self.camera, self.LAYER_PLATFORM)

        # self.tilemap.draw_layer(self.viewport, self.camera, self.LAYER_BG_PURPLE, self.PALETTE['purple'])
        # self.tilemap.draw_layer(self.viewport, self.camera, self.LAYER_BG_RED,    self.PALETTE['red'])
        # self.tilemap.draw_layer(self.viewport, self.camera, self.LAYER_BG_GREEN,  self.PALETTE['green'])
        # self.tilemap.draw_layer(self.viewport, self.camera, self.LAYER_BG_CREAM,  self.PALETTE['cream'])

        # self.tilemap.draw_layer(self.viewport, self.camera, self.LAYER_BACKGROUND,  (128, 128, 128))
        # self.tilemap.draw_layer(self.viewport, self.camera, self.LAYER_BACKGROUND2, (180, 180, 180))
        
        # self.tilemap.draw_layer(self.viewport, self.camera, self.LAYER_PLATFORM_PURPLE, self.PALETTE['purple'])
        # self.tilemap.draw_layer(self.viewport, self.camera, self.LAYER_PLATFORM_RED,    self.PALETTE['red'])
        # self.tilemap.draw_layer(self.viewport, self.camera, self.LAYER_PLATFORM_GREEN,  self.PALETTE['green'])
        # self.tilemap.draw_layer(self.viewport, self.camera, self.LAYER_PLATFORM_CREAM,  self.PALETTE['cream'])

        camera_pos = self.camera.get_pos()
        self.viewport.blit(self.platform_surface, (-camera_pos[0], -camera_pos[1]))

        player_is_dead = self.player.state == PlayerState.DEAD

        # When decoy is active, enemies chase the guardian instead of the player
        if self.guardian.state == GuardianState.DECOY:
            enemy_target = self.guardian.rect
        else:
            enemy_target = self.player.rect

        decoy_active = self.guardian.state == GuardianState.DECOY
        new_entities = []
        for entity in self.entities:
            if isinstance(entity, Spike):
                continue
            elif isinstance(entity, Boss):
                if not player_is_dead:
                    result = entity.update(self.player.rect)
                    # Seal the arena the moment the boss wakes up
                    if not self.arena_locked and entity.state == BossState.SPAWNING:
                        self.arena_locked = True
                    if result:
                        new_entities.extend(result['projectiles'])
                        if result['ghosts'] > 0:
                            boss_cx = int(entity.pos[0]) + Tileset.TILE_SIZE * 2
                            boss_y  = int(entity.pos[1])
                            offset  = Tileset.TILE_SIZE * 5
                            ghost_l = Ghost(boss_cx - offset, boss_y)
                            ghost_r = Ghost(boss_cx + offset, boss_y)
                            ghost_l.direction = -1
                            new_entities.extend([ghost_l, ghost_r])
                        if result['defeated']:
                            self.boss_defeated  = True
                            self._credits_timer = FPS * 3  # 3-second pause before credits
                        # Copy-player collision — touching a copy teleports the boss there
                        for copy in entity.copies:
                            _offset = Tileset.TILE_SIZE
                            copy_rect = pygame.Rect(
                                int(copy.pos[0]) + _offset, int(copy.pos[1]) + _offset,
                                Tileset.TILE_SIZE * 2, Tileset.TILE_SIZE * 2
                            )
                            if copy_rect.colliderect(self.player.rect):
                                entity.snap_to_copy(copy)
                                break
                entity.draw(self.viewport, self.camera)
            elif isinstance(entity, Checkpoint):
                entity.draw(self.viewport, self.camera)
                if not entity.activated and not player_is_dead:
                    if entity.rect.colliderect(self.player.rect):
                        entity.activated = True
                        self._save_checkpoint(entity)
            else:
                if entity.type in (EntityType.GHOST, EntityType.SPIDER):
                    entity.distracted = decoy_active
                if not player_is_dead:
                    result = entity.update(enemy_target)
                    if result is not None:
                        new_entities.append(result)
                entity.draw(self.viewport, self.camera)
        self.entities.extend(new_entities)

        # Guardian drawn AFTER viewport.fill() so it's not wiped - fixes the guardian bug too
        self.guardian.update()
        self.guardian.draw(self.viewport, self.camera)

        if not player_is_dead:
            # Check projectile collisions
            projectiles = [e for e in self.entities if e.type == EntityType.PROJECTILE]
            ghosts = [e for e in self.entities if e.type == EntityType.GHOST]
            webs = [e for e in self.entities if e.type == EntityType.SPIDER_WEB]
            spiders = [e for e in self.entities if e.type == EntityType.SPIDER]
            web_zones = [e for e in self.entities if e.type == EntityType.WEB_ZONE]

            for projectile in projectiles:
                # Remove if off screen
                if projectile.x < 0 or projectile.x > self.tilemap.width * Tileset.TILE_SIZE:
                    projectile.collected = True
                    continue

                # Check against each ghost
                for ghost in ghosts:
                    if not ghost.collected and projectile.rect.colliderect(ghost.rect):
                        ghost.hit()
                        projectile.collected = True
                        break
                for spider in spiders:
                    if not spider.collected and projectile.rect.colliderect(spider.rect):
                        spider.hit()
                        projectile.collected = True
                        break
                # Destroy web zone
                for web_zone in web_zones:
                    if not web_zone.collected and projectile.rect.colliderect(web_zone.rect):
                        web_zone.collected = True
                        projectile.collected = True
                        break
                # Hit boss
                if not projectile.collected:
                    for entity in self.entities:
                        if isinstance(entity, Boss) and not entity.collected:
                            if projectile.rect.colliderect(entity.rect):
                                entity.hit()
                                projectile.collected = True
                                break

            # Destroy spider web projectile if it hits a solid tile
            for web in webs:
                if web.collected:
                    continue
                web_tile_x = web.x // Tileset.TILE_SIZE
                web_tile_y = web.y // Tileset.TILE_SIZE
                tiles_around = self._get_all_platform_tiles(
                    pygame.Rect(web_tile_x - 1, web_tile_y - 1, 3, 3)
                )
                for row in tiles_around:
                    for tile in row:
                        if tile.type in (TileType.NONE, TileType.LADDER, TileType.CHAIN):
                            continue
                        if web.rect.colliderect(tile.rect):
                            web.collected = True
                            break
                    if web.collected:
                        break

            # Sword hit detection — triggers dying animation same as projectile kills
            if self.player.sword_rect:
                from src.entities.ghost import GhostState
                for entity in self.entities:
                    if entity.type not in (EntityType.GHOST, EntityType.SPIDER):
                        continue
                    if getattr(entity, 'collected', False):
                        continue
                    if entity.type == EntityType.GHOST and entity.state == GhostState.DYING:
                        continue
                    if entity.type == EntityType.SPIDER and entity.state.name == 'DEAD':
                        continue
                    if self.player.sword_rect.colliderect(entity.rect):
                        if entity.type == EntityType.GHOST:
                            entity.state = GhostState.DYING
                            entity.death_timer = FPS
                        elif entity.type == EntityType.SPIDER:
                            entity.hit()
                # Sword reflects boss projectiles (unreflected only)
                for entity in self.entities:
                    if (entity.type == EntityType.BOSS_PROJECTILE
                            and not entity.collected
                            and not entity.reflected
                            and self.player.sword_rect.colliderect(entity.rect)):
                        entity.reflect()
                # Sword hits boss
                for entity in self.entities:
                    if isinstance(entity, Boss) and not entity.collected:
                        if self.player.sword_rect.colliderect(entity.rect):
                            entity.hit()

            # Boss projectile collision and off-screen cleanup
            boss_projectiles = [e for e in self.entities if e.type == EntityType.BOSS_PROJECTILE]
            for proj in boss_projectiles:
                if (proj.x < 0 or proj.x > self.tilemap.width * Tileset.TILE_SIZE or
                        proj.y < 0 or proj.y > self.tilemap.height * Tileset.TILE_SIZE):
                    proj.collected = True
                    continue
                if proj.reflected:
                    # Reflected projectiles damage the boss, not the player
                    for entity in self.entities:
                        if isinstance(entity, Boss) and not entity.collected:
                            if proj.rect.colliderect(entity.rect):
                                entity.hit()
                                proj.collected = True
                                break
                elif proj.rect.colliderect(self.player.rect):
                    proj.collected = True
                    if self.player.follow and self.player.follow.shield_active:
                        self.player.follow.break_shield()
                        self.player._invulnerability_timer = self.player.INVULNERABILITY_DURATION
                    elif self.player._invulnerability_timer <= 0:
                        self.player.change_state_to(PlayerState.DEAD)

            # Handle upgrade jewel collection
            for entity in self.entities:
                if isinstance(entity, UpgradeJewel) and entity.collected:
                    self.charges = self.MAX_CHARGES
                    if entity.level == 3:
                        self.guardian.trigger_level3_upgrade()
                    else:
                        self.guardian.trigger_upgrade()

            # Handle regular jewel collection
            for entity in self.entities:
                if isinstance(entity, Jewel) and not isinstance(entity, UpgradeJewel) and entity.collected:
                    self.charges = min(self.charges + 1, self.MAX_CHARGES)

            # Now remove all collected entities in one pass
            self.entities = [e for e in self.entities
                            if not getattr(e, 'collected', False)]

        self.player.draw(self.viewport, self.camera)

        self.surface.blit(self.viewport, (0, 8*3))

        # Count down to credits after boss death
        if self.boss_defeated and self._credits_timer > 0:
            self._credits_timer -= 1
            if self._credits_timer == 0:
                next_state = LevelState.BOSS_DEFEATED

        return next_state
