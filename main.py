import pygame
import asyncio

from src.constants import *
import src.gamepad as Gamepad
import src.tileset as Tileset
from src.scenes import *

async def main():
    # pygame setup
    pygame.init()
    pygame.mixer.pre_init()
    screen = pygame.display.set_mode(WINDOW_SIZE, flags=pygame.RESIZABLE)
    clock = pygame.time.Clock() # Clock used to handle frame rate

    canvas = pygame.Surface(SCREEN_SIZE)

    Tileset.init()
    Gamepad.init()
    
    scenes = [
        Menu(canvas),
        Controls(canvas),
        Game(canvas),
        Credits(canvas),
        GameOver(canvas)
    ]

    #current_scene = Menu(canvas)
    current_scene = 0

    previous_display_size = pygame.display.get_window_size()

    running = True
    while running:
        events = pygame.event.get()

        for event in events:
            match event.type:
                case pygame.QUIT:
                    running = False
                case pygame.KEYDOWN:
                    match event.key:
                        case pygame.K_ESCAPE:
                            running = False
                        case pygame.K_f:
                            if pygame.display.is_fullscreen():
                                pygame.display.toggle_fullscreen()
                                screen = pygame.display.set_mode(previous_display_size, flags=pygame.RESIZABLE)
                            else:
                                previous_display_size = pygame.display.get_window_size()
                                pygame.display.toggle_fullscreen()
                case pygame.JOYDEVICEADDED:
                    Gamepad.init()

        # Scene state manager
        match scenes[current_scene].update(events):
            case SceneState.MENU:
                current_scene = 0
                scenes[2].reset()
            case SceneState.CONTROLS:
                current_scene = 1
            case SceneState.GAME:
                current_scene = 2
            case SceneState.CREDITS:
                current_scene = 3
            case SceneState.GAME_OVER:
                current_scene = 4
                scenes[4].play_music()
                scenes[2].reset_current_level()
            case SceneState.NO_CHANGE:
                pass
            case _:
                raise Exception("Unknown state!")
            

        # Update the screen (flip() swaps the backbuffer and framebuffer)
        # Tileset.render_tile(canvas, Tileset.render_string(f"{int(clock.get_fps())}"), 27, 0)
        window_size = pygame.display.get_window_size()
        scaled_size = list(window_size)
        position = [0, 0]
        if window_size[0] > window_size[1]:
            scale = window_size[1]/SCREEN_SIZE[1]
            scaled_size[0] = SCREEN_SIZE[0]*scale
            position[0] = (window_size[0]/2)-(scaled_size[0]/2)
        else:
            scale = window_size[0]/SCREEN_SIZE[0]
            scaled_size[1] = SCREEN_SIZE[1]*scale
            position[1] = (window_size[1]/2)-(scaled_size[1]/2)

        scaled_screen = pygame.Surface(scaled_size)
        
        pygame.transform.scale(canvas, scaled_size, scaled_screen)
        screen.fill((0, 0, 0))
        screen.blit(scaled_screen, position)

        pygame.display.flip()

        clock.tick(FPS)  # limits FPS to 60
        await asyncio.sleep(0)

    pygame.quit()

if __name__=="__main__":
    asyncio.run(main())