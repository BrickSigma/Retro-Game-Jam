"""
Controls screen
"""

from src.scenes import Scene, SceneState
import src.tileset as Tileset
import pygame

class Controls(Scene):
    def __init__(self, surface):
        super().__init__(surface)
        self.text = Tileset.render_string("WASD/Arrow keys to move")

    def update(self, events):
        next_state = SceneState.NO_CHANGE

        for event in events:
            match event.type:
                case pygame.KEYDOWN:
                    if event.key == pygame.K_BACKSPACE:
                        next_state = SceneState.MENU
                case pygame.JOYBUTTONDOWN:
                    if event.button == 1:
                        next_state = SceneState.MENU

        self.surface.fill((0, 0, 0))
        Tileset.render_tile(self.surface, self.text, 0, 0)

        return next_state