"""
End credits scene
"""

from src.scenes import Scene, SceneState
from src.tileset import TextBox, GREY, LIGHT_BLUE
import pygame
from src.constants import resource_path

class Credits(Scene):
    def __init__(self, surface):
        super().__init__(surface)
        self.background = pygame.image.load(resource_path("assets/levels/credits-screen.png"))

        self.texts = [
            TextBox("Developers:", 2, 5, 0, 0),
            TextBox("Clyde and Junaid", 13, 5, 0, 0, GREY),

            TextBox("SFX:", 2, 7, 0, 0),
            TextBox("Vinit and Tim", 6, 7, 0, 0, GREY),

            TextBox("Playtesters:", 2, 9, 0, 0),
            TextBox("Martha and Lee",14, 9, 0, 0, GREY),

            TextBox("Tilesets by:", 2, 12, 0, 0),
            TextBox("willian mstach", 2, 13, color=GREY),
            TextBox("Kappa Mimic", 2, 14, color=GREY),

            TextBox("Music by:", 18, 12, 0, 0),
            TextBox("Diablo Luna", 18, 13, color=GREY),

            TextBox("SFX sourced from:", 2, 17, 0, 0),
            TextBox("pixabay.com", 19, 17, 0, 0, GREY)
        ]

    def update(self, events):
        next_state = SceneState.NO_CHANGE

        for event in events:
            match event.type:
                case pygame.KEYDOWN:
                    if event.key in (pygame.K_BACKSPACE, pygame.K_RETURN):
                        next_state = SceneState.MENU
                case pygame.JOYBUTTONDOWN:
                    if event.button in (0, 1):
                        next_state = SceneState.MENU

        self.surface.blit(self.background)

        for text in self.texts:
            text.draw(self.surface)

        return next_state