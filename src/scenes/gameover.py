from src.scenes.scene import Scene, SceneState
import pygame
import src.tileset as Tileset
from src.tileset import TileType
import src.gamepad as Gamepad

class GameOver(Scene):
    COLORS = [
        (255, 0, 0),
        (255, 165, 0),
    ]

    def __init__(self, surface):
        super().__init__(surface)
        self.title       = Tileset.render_string("Game Over")
        self.retry       = Tileset.render_string("Retry")
        self.menu        = Tileset.render_string("Menu")
        self.arrow       = Tileset.get_tile(TileType.ARROW.value)
        self.selected    = 0
        self.counter     = 0
        self.color       = 0
    
    def update(self) -> SceneState:
        next_state = SceneState.NO_CHANGE

        # Handle joystick input
        joystick = Gamepad.get_joystick()
        if joystick is not None:
            y_axis = joystick.get_axis(Gamepad.LEFT_Y_AXIS)
            if y_axis < -Gamepad.AXIS_THESHOLD:
                self.selected = 0
            elif y_axis > Gamepad.AXIS_THESHOLD:
                self.selected = 1

        for event in pygame.event.get():
            match event.type:
                case pygame.QUIT:
                    next_state = SceneState.QUIT
                case pygame.KEYDOWN:
                    match event.key:
                        case pygame.K_ESCAPE:
                            next_state = SceneState.QUIT
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
        
        self.surface.fill((0,0,0))

        # Tile - rendered in the upper middle area
        Tileset.render_tile(self.surface, self.title, 10, 6)

        # Draw 3 hearts greyed out to show all lives lost
        heart = Tileset.get_tile(TileType.HEART.value)
        grey_heart = Tileset.change_letter_color(heart, (80,80,80))
        for i in range(3):
            Tileset.render_tile(self.surface, grey_heart, 13 + i, 10)
        
        # Menu options
        Tileset.render_tile(self.surface, self.retry, 12, 16)
        Tileset.render_tile(self.surface, self.menu, 12, 18)

        # Animated arrow next to selected option
        for i in range(2):
            arrow = self.arrow
            if i == self.selected:
                arrow = Tileset.change_letter_color(arrow, self.COLORS[self.color])
            Tileset.render_tile(self.surface, arrow, 10, 16 + (i * 2))

        # Cycle arrow color
        self.counter += 1
        if self.counter % 25 == 0:
            self.color = (self.color + 1) % len(self.COLORS)
        
        return next_state