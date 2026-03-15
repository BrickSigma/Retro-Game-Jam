import pygame
import asyncio

from src.constants import *
import src.tileset as Tileset
from src.scenes.menu import Menu
from src.scenes.scene import SceneState

"""
The game is wrapped in the `main` function below which has also been made asynchronous.

The reason for this is to support a web build of the game (that we can upload to itch.io).
It'll still run perfectly on desktop.
"""
async def main():
    # pygame setup
    pygame.init()
    screen = pygame.display.set_mode(WINDOW_SIZE)
    clock = pygame.time.Clock() # Clock used to handle frame rate

    canvas = pygame.Surface(SCREEN_SIZE)

    Tileset.init()

    current_scene = Menu(canvas)

    running = True
    while running:
        if current_scene.update() == SceneState.QUIT:
            running = False

        # Update the screen (flip() swaps the backbuffer and framebuffer)
        pygame.transform.scale(canvas, WINDOW_SIZE, screen)
        pygame.display.flip()

        clock.tick(FPS)  # limits FPS to 60
        await asyncio.sleep(0)  # Needed for web build

    pygame.quit()

asyncio.run(main())