from src.scenes.scene import Scene, SceneState
import pygame
import src.tileset as Tileset
from src.constants import resource_path
import src.gamepad as Gamepad

class GameOver(Scene):
    MAX_JOYSTICK_DELAY = 20
    LIGHT_BLUE = (203, 219, 252)

    def __init__(self, surface):
        super().__init__(surface)
        self.background = pygame.image.load(resource_path("assets/levels/game-over-screen.png"))
        
        self.retry = Tileset.change_letter_color(Tileset.render_string("Retry"), self.LIGHT_BLUE)
        self.menu = Tileset.change_letter_color(Tileset.render_string("Menu"), self.LIGHT_BLUE)
        
        self.selected    = 0

        self.arrow = Tileset.change_letter_color(Tileset.get_tile(39), self.LIGHT_BLUE)
        self.selected = 0
        self.joystick_delay = 0

    def play_music(self):
        pygame.mixer.music.load(resource_path("assets/music/game-over.ogg"))
        pygame.mixer.music.play(1)
    
    def update(self, events) -> SceneState:
        next_state = SceneState.NO_CHANGE

        # Decrease the joystick delay each frame so that it doesn't immediately go to the bottom
        self.joystick_delay -= 1
        if self.joystick_delay < 0:
            self.joystick_delay = 0

        # Handle joystick input
        joystick = Gamepad.get_joystick()
        if joystick is not None:
            y_axis = joystick.get_axis(Gamepad.LEFT_Y_AXIS)
            if y_axis < -Gamepad.AXIS_THESHOLD and self.joystick_delay == 0:
                self.selected = 0
                self.joystick_delay = self.MAX_JOYSTICK_DELAY
            elif y_axis > Gamepad.AXIS_THESHOLD and self.joystick_delay == 0:
                self.selected = 1
                self.joystick_delay = self.MAX_JOYSTICK_DELAY

        for event in events:
            match event.type:
                case pygame.KEYDOWN:
                    match event.key:
                        case pygame.K_DOWN | pygame.K_s:
                            self.selected = 1
                        case pygame.K_UP | pygame.K_w:
                            self.selected = 0
                        case pygame.K_RETURN:
                            if self.selected == 0:
                                next_state = SceneState.GAME # Restart the game
                            else:
                                next_state = SceneState.MENU # back to menu
                case pygame.JOYBUTTONDOWN:
                    if event.button == 0:
                        if self.selected == 0:
                            next_state = SceneState.GAME # Restart the game
                        else:
                            next_state = SceneState.MENU # back to menu
        
        self.surface.blit(self.background)
        
        # Menu options
        Tileset.render_tile(self.surface, self.retry, 14, 11)
        Tileset.render_tile(self.surface, self.menu, 14, 13)

        Tileset.render_tile(self.surface, self.arrow, 12, 11 + self.selected*2)
        
        return next_state