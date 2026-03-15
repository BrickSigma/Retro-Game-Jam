from src.scenes.scene import Scene, SceneState
import pygame
import src.tileset as Tileset

class Menu(Scene):
    def __init__(self, surface):
        super().__init__(surface)
        self.title = Tileset.get_string("Retro Game Jam")

    def update(self) -> SceneState:
        next_state = SceneState.MENU

        for event in pygame.event.get():
            match event.type:
                case pygame.QUIT:
                    next_state = SceneState.QUIT

        self.surface.fill((255, 255, 255))
        Tileset.render_tile(self.surface, self.title, 4, 12)

        return next_state
