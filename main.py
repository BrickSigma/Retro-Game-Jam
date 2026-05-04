import pygame
import asyncio

from src.constants import *
import src.tileset as Tileset
from src.scenes import *

async def main():
    # pygame setup
    pygame.init()
    screen = pygame.display.set_mode(WINDOW_SIZE)
    clock = pygame.time.Clock() # Clock used to handle frame rate

    canvas = pygame.Surface(SCREEN_SIZE)

    Tileset.init()

    #current_scene = Menu(canvas)
    current_scene = Game(canvas)

    running = True
    while running:
        # Scene state manager
        match current_scene.update():
            case SceneState.QUIT:
                running = False
            case SceneState.MENU:
                current_scene = Menu(canvas)
            case SceneState.CONTROLS:
                current_scene = Controls(canvas)
            case SceneState.GAME:
                current_scene = Game(canvas)
            case SceneState.CREDITS:
                current_scene = Credits(canvas)
            case SceneState.GAME_OVER:
                current_scene = GameOver(canvas)
            case SceneState.NO_CHANGE:
                pass
            case _:
                raise Exception("Unknown state!")
            

        # Update the screen (flip() swaps the backbuffer and framebuffer)
        Tileset.render_tile(canvas, Tileset.render_string(f"{int(clock.get_fps())}"), 27, 0)
        pygame.transform.scale(canvas, WINDOW_SIZE, screen)

        pygame.display.flip()

        clock.tick(FPS)  # limits FPS to 60
        await asyncio.sleep(0)

    pygame.quit()

if __name__=="__main__":
    asyncio.run(main())