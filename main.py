# /// script
# dependencies = ["pytmx"]
# ///

import pygame
import asyncio
import pytmx
import sys

if sys.platform == "emscripten":
    import platform as _web_platform
else:
    _web_platform = None

from src.constants import *
import src.gamepad as Gamepad
import src.tileset as Tileset
from src.scenes import *

async def main():
    print("[init] starting")
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init()

    # Force nearest-neighbor (pixelated) canvas rendering in the browser.
    # Without this, browsers apply bilinear interpolation which blurs pixel art.
    if _web_platform is not None:
        _web_platform.window.canvas.style.imageRendering = "pixelated"

    print("[init] pygame.init done")
    screen = pygame.display.set_mode(WINDOW_SIZE, flags=pygame.RESIZABLE)
    clock = pygame.time.Clock()
    canvas = pygame.Surface(SCREEN_SIZE)

    print("[init] loading tileset")
    Tileset.init()
    Gamepad.init()

    print("[init] creating scenes")
    scenes = [
        Menu(canvas),
        Controls(canvas),
        Game(canvas),
        Credits(canvas),
        GameOver(canvas)
    ]
    print("[init] all scenes ready")

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
                            # On web, Escape is handled by the browser to exit
                            # fullscreen — quitting the game loop would just blank
                            # the page, which is confusing.
                            if _web_platform is None:
                                running = False
                        case pygame.K_f:
                            if _web_platform is not None:
                                try:
                                    if _web_platform.window.document.fullscreenElement:
                                        _web_platform.window.document.exitFullscreen()
                                    else:
                                        _web_platform.window.document.documentElement.requestFullscreen()
                                except Exception:
                                    pass
                            else:
                                if pygame.display.is_fullscreen():
                                    pygame.display.toggle_fullscreen()
                                    screen = pygame.display.set_mode(previous_display_size, flags=pygame.RESIZABLE)
                                else:
                                    previous_display_size = pygame.display.get_window_size()
                                    pygame.display.toggle_fullscreen()
                case pygame.JOYBUTTONDOWN:
                    if event.button == 6:
                        if _web_platform is not None:
                            try:
                                if _web_platform.window.document.fullscreenElement:
                                    _web_platform.window.document.exitFullscreen()
                                else:
                                    _web_platform.window.document.documentElement.requestFullscreen()
                            except Exception:
                                pass
                        else:
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

        # NOTE: On screens smaller than 256x240, scale clamps to 1x.
        # The game will extend beyond the screen edges rather than shrink below
        # 1x scale — this is preferable to a blurry sub-pixel render.
        scale = max(1, min(
            window_size[0] // SCREEN_SIZE[0],
            window_size[1] // SCREEN_SIZE[1]
        ))

        scaled_w = SCREEN_SIZE[0] * scale
        scaled_h = SCREEN_SIZE[1] * scale

        # Center the scaled game canvas in the window
        position = (
            (window_size[0] - scaled_w) // 2,
            (window_size[1] - scaled_h) // 2
        )

        scaled_screen = pygame.Surface((scaled_w, scaled_h))
        pygame.transform.scale(canvas, (scaled_w, scaled_h), scaled_screen)
        screen.fill((0, 0, 0))
        screen.blit(scaled_screen, position)

        pygame.display.flip()

        clock.tick(FPS)  # limits FPS to 60
        await asyncio.sleep(0)

    pygame.quit()

if __name__=="__main__":
    asyncio.run(main())