from src.scenes.scene import Scene, SceneState
import pygame
import src.tileset as Tileset

class Menu(Scene):
    COLORS = [
        (255, 0, 0),
        (0, 0, 255)
    ]

    def __init__(self, surface):
        super().__init__(surface)
        self.title = Tileset.get_string("Retro Game Jam")
        self.start_button = Tileset.get_string("Start")
        self.controls_button = Tileset.get_string("Controls")
        self.arrow = Tileset.get_tile(39)
        self.selected = 0
        self.counter = 0
        self.color = 0

    def update(self) -> SceneState:
        next_state = SceneState.NO_CHANGE

        for event in pygame.event.get():
            match event.type:
                case pygame.QUIT:
                    next_state = SceneState.QUIT
                case pygame.KEYDOWN:
                    match event.key:
                        case pygame.K_ESCAPE:
                            next_state = SceneState.QUIT
                        case pygame.K_DOWN:
                            self.selected = 1
                        case pygame.K_UP:
                            self.selected = 0
                        case pygame.K_s:
                            self.selected = 1
                        case pygame.K_w:
                            self.selected = 0

                        case pygame.K_RETURN:
                            if self.selected == 0:
                                next_state = SceneState.GAME
                            else:
                                next_state = SceneState.CONTROLS

        self.surface.fill((255, 255, 255))
        Tileset.render_tile(self.surface, self.title, 9, 6)
        Tileset.render_tile(self.surface, self.start_button, 12, 20)
        Tileset.render_tile(self.surface, self.controls_button, 12, 22)

        for i in range(0, 4, 2):
            arrow = self.arrow
            if i/2 == self.selected:
                arrow = Tileset.swap_color(arrow, (0, 0, 0), self.COLORS[self.color])
            Tileset.render_tile(self.surface, arrow, 10, 20 + i)

        self.counter += 1
        if self.counter % 25 == 0:
            self.color += 1
            self.color %= len(self.COLORS)

        return next_state
