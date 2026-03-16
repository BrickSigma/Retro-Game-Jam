"""
Game scene module: this holds the actual playable game.
"""

from src.scenes import Scene, SceneState
import src.tileset as Tileset
import pygame

class Game(Scene):
    def __init__(self, surface):
        super().__init__(surface)
        self.text = Tileset.get_string("Main Game")

    def update(self):
        """Main game loop sits here"""
        next_state = SceneState.NO_CHANGE

        for event in pygame.event.get():
            match event.type:
                case pygame.QUIT:
                    next_state = SceneState.QUIT
                case pygame.KEYDOWN:
                    match event.key:
                        case pygame.K_ESCAPE:
                            next_state = SceneState.QUIT
                        case pygame.K_BACKSPACE:
                            next_state = SceneState.MENU

        self.surface.fill((255, 255, 255))
        Tileset.render_tile(self.surface, self.text, 0, 0)

        return next_state