from src.scenes.scene import Scene, SceneState
import pygame
import src.tileset as Tileset
import src.gamepad as Gamepad

class Menu(Scene):
    COLORS = [
        (255, 0, 0),
        (0, 0, 255)
    ]

    def __init__(self, surface):
        super().__init__(surface)
        self.title = Tileset.render_string("Retro Game Jam")
        self.start_button = Tileset.render_string("Start")
        self.controls_button = Tileset.render_string("Controls")
        self.arrow = Tileset.get_tile(39)
        self.selected = 0
        self.counter = 0
        self.color = 0

    def update(self, events) -> SceneState:
        next_state = SceneState.NO_CHANGE

        # Handle joystick input
        joystick = Gamepad.get_joystick()
        if joystick is not None:
            y_axis = joystick.get_axis(Gamepad.LEFT_Y_AXIS)
            if y_axis < -Gamepad.AXIS_THESHOLD:
                self.selected = 0
            elif y_axis > Gamepad.AXIS_THESHOLD:
                self.selected = 1

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
                                next_state = SceneState.GAME
                            else:
                                next_state = SceneState.CONTROLS

                case pygame.JOYBUTTONDOWN:
                    if event.button == 0:
                        if self.selected == 0:
                            next_state = SceneState.GAME
                        else:
                            next_state = SceneState.CONTROLS

        self.surface.fill((0, 0, 0))
        Tileset.render_tile(self.surface, self.title, 9, 6)
        Tileset.render_tile(self.surface, self.start_button, 12, 20)
        Tileset.render_tile(self.surface, self.controls_button, 12, 22)

        for i in range(0, 4, 2):
            arrow = self.arrow
            if i/2 == self.selected:
                arrow = Tileset.change_letter_color(arrow, self.COLORS[self.color])
            Tileset.render_tile(self.surface, arrow, 10, 20 + i)

        self.counter += 1
        if self.counter % 25 == 0:
            self.color += 1
            self.color %= len(self.COLORS)

        return next_state
