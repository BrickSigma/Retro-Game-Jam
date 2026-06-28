from src.scenes.scene import Scene, SceneState
import pygame
import src.tileset as Tileset
import src.gamepad as Gamepad
from src.constants import resource_path

class Menu(Scene):
    MAX_JOYSTICK_DELAY = 20
    LIGHT_BLUE = (203, 219, 252)

    def __init__(self, surface):
        super().__init__(surface)

        self.background = pygame.image.load(resource_path("assets/levels/title-screen.png"))

        self.start_button = Tileset.change_letter_color(Tileset.render_string("Play"), self.LIGHT_BLUE)
        self.controls_button = Tileset.change_letter_color(Tileset.render_string("Controls"), self.LIGHT_BLUE)
        self.credits_button = Tileset.change_letter_color(Tileset.render_string("Credits"), self.LIGHT_BLUE)

        self.arrow = Tileset.change_letter_color(Tileset.get_tile(39), self.LIGHT_BLUE)
        self.selected = 0
        self.joystick_delay = 0

    def select_below(self):
        self.selected += 1
        if self.selected > 2:
            self.selected = 2

    def select_above(self):
        self.selected -= 1
        if self.selected < 0:
            self.selected = 0

    def handle_music(self):
        """
        Used to handle the background music for the game.
        """
        if pygame.mixer.music.get_busy():
            return  # Do nothing if it's already playing a track
        
        pygame.mixer.music.load(f"assets/music/peaceful.wav")
            
        pygame.mixer.music.set_volume(0.2)
        pygame.mixer.music.play(fade_ms=2000)

    def update(self, events) -> SceneState:
        next_state = SceneState.NO_CHANGE

        self.handle_music()

        # Decrease the joystick delay each frame so that it doesn't immediately go to the bottom
        self.joystick_delay -= 1
        if self.joystick_delay < 0:
            self.joystick_delay = 0

        # Handle joystick input
        joystick = Gamepad.get_joystick()
        if joystick is not None:
            y_axis = joystick.get_axis(Gamepad.LEFT_Y_AXIS)
            if y_axis < -Gamepad.AXIS_THESHOLD and self.joystick_delay == 0:
                self.select_above()
                self.joystick_delay = self.MAX_JOYSTICK_DELAY
            elif y_axis > Gamepad.AXIS_THESHOLD and self.joystick_delay == 0:
                self.select_below()
                self.joystick_delay = self.MAX_JOYSTICK_DELAY

        for event in events:
            match event.type:
                case pygame.KEYDOWN:
                    match event.key:
                        case pygame.K_DOWN | pygame.K_s:
                            self.select_below()
                        case pygame.K_UP | pygame.K_w:
                            self.select_above()
                        case pygame.K_RETURN:
                            match (self.selected):
                                case 0:
                                    next_state = SceneState.GAME
                                case 1: 
                                    next_state = SceneState.CONTROLS
                                case 2:
                                    next_state = SceneState.CREDITS

                case pygame.JOYBUTTONDOWN:
                    if event.button == 0:
                        if self.selected == 0:
                            next_state = SceneState.GAME
                        else:
                            next_state = SceneState.CONTROLS

        self.surface.fill((0, 0, 0))

        self.surface.blit(self.background)

        Tileset.render_tile(self.surface, self.start_button, 12, 23)
        Tileset.render_tile(self.surface, self.controls_button, 12, 25)
        Tileset.render_tile(self.surface, self.credits_button,  12, 27)

        Tileset.render_tile(self.surface, self.arrow, 10, 23 + self.selected*2)

        return next_state
