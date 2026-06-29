"""
Controls screen
"""

from src.scenes import Scene, SceneState
from src.tileset import TextBox, GREY, LIGHT_BLUE
import pygame

from src.constants import resource_path

class Controls(Scene):
    def __init__(self, surface):
        super().__init__(surface)

        self.background = pygame.image.load(resource_path("assets/levels/controls.png"))

        self.texts = [
            TextBox("Keyboard", 12, 4, color=GREY),
            TextBox("Joystick", 22, 4, color=GREY),

            TextBox("Move", 4, 7, color=GREY),
            TextBox("WASD", 14, 7),
            TextBox("Joystick", 22, 7),

            TextBox("Jump", 4, 10, color=GREY),
            TextBox("Space", 14, 10, 0),
            TextBox("A Button", 22, 10),

            TextBox("Platform", 2, 13, color=GREY),
            TextBox("L", 16, 13, 0),
            TextBox("B Button", 22, 13),

            TextBox("Shoot", 4, 16, 0, color=GREY),
            TextBox("K", 16, 16, 0),
            TextBox("X Button", 22, 16),

            TextBox("Jump Pad", 2, 19, color=GREY),
            TextBox("O", 16, 19, 0),
            TextBox("Y Button", 22, 19),

            TextBox("Shield", 3, 22, color=GREY),
            TextBox("P", 16, 22, 0),
            TextBox("LB", 25, 22)
        ]

        self.counter = 0
        self.color = 0

        self.COLORS = [LIGHT_BLUE, GREY]

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

        self.surface.blit(self.background)
        for text in self.texts:
            text.draw(self.surface)

        if (self.counter % 30) == 0:
            self.color = (self.color + 1) % 2

        self.counter += 1

        TextBox("Return to menu", 9, 27, 0, 0, self.COLORS[self.color]).draw(self.surface)

        return next_state