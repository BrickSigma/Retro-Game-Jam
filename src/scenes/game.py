"""
Game scene module: this holds the actual playable game.
"""

from src.scenes import Scene, SceneState
import src.tileset as Tileset
from src.level import Level, LevelState
from src.camera import CameraState

class Game(Scene):
    def __init__(self, surface):
        super().__init__(surface)
        self.text = Tileset.render_string("Main Game")

        print("[init] loading level 1")
        self.levels = [
            Level(
                self.surface,
                1, "peaceful.ogg",
                background_layer=True,
                text_guides=[
                        Tileset.GuideText("Use A/D to move to the gate", (16, 24)),
                        Tileset.GuideText("Press space to jump", (16, 40))
                ],
                unload_music=False
            ),
        ]
        print("[init] loading level 2")
        self.levels.append(Level(
                self.surface,
                2, "peaceful.ogg",
                background_layer=True,
                text_guides=[
                    Tileset.GuideText("Watch out for ghosts!", (16, 24)),
                    Tileset.GuideText("Press K to shoot", (16, 40)),
                    Tileset.GuideText("Spawn a platform", (240, 24)),
                    Tileset.GuideText("Press L", (240, 40))
                ],
                unload_music=False
            ))
        print("[init] loading level 3")
        self.levels.append(Level(
                self.surface,
                3, "peaceful.ogg",
                background_layer=True,
                text_guides=[
                    Tileset.GuideText("Good luck!", (16, 24))
                ]))
        print("[init] loading level 4")
        self.levels.append(Level(self.surface, 4, "techno.ogg", CameraState.VERTICAL, hud_background=(32, 34, 54), background_layer=False))
        print("[init] loading level 5")
        self.levels.append(Level(self.surface, 5, "difficult.ogg", background_layer=True))
        print("[init] all levels loaded")

        self.current_level = 0
        self.level = self.levels[self.current_level]

    def reset(self):
        for level in self.levels:
            level.restart()

        self.current_level = 0
        self.level = self.levels[self.current_level]

    def reset_current_level(self):
        self.level.restart()

    def next_level(self):
        """Move to the next level, carrying over earned upgrades."""
        banked = self.level.guardian.get_upgrade_state()
        self.current_level += 1
        self.level = self.levels[self.current_level]
        self.level.apply_banked_upgrades(banked)

    def update(self, events):
        """Main game loop sits here"""
        next_state = SceneState.NO_CHANGE

        match self.level.update(events):
            case LevelState.NEXT_LEVEL:
                if (self.current_level + 1) >= len(self.levels):
                    next_state = SceneState.CREDITS
                else:
                    self.next_level()
            case LevelState.GAME_OVER:
                next_state = SceneState.GAME_OVER
            case LevelState.BOSS_DEFEATED:
                next_state = SceneState.CREDITS
            case LevelState.NO_CHANGE:
                pass

        return next_state