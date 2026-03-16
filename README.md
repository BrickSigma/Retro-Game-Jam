# 8bits to Infinity Retro Game Jam
This is our repository code for the 2026 8bits to Infinity Retro Game Jam submission. The game is built using Python and Pygame.

## Project Stucture
The project is structured in the following way (as of now):
```
.
└── project/
    ├── assets/
    │   └── tileset.png
    ├── src/
    │   ├── game/
    │   │   └── game code
    │   ├── scenes/
    │   │   ├── scene.py
    │   │   └── menu/game/credits scene files
    │   ├── constants.py
    │   └── tileset.py
    └── main.py
```

`main.py` is the entry point for the game. It manages a global ***scene manager*** which allows switching between the menu, credits, and actual game loop.

Other Python files are located in the `src` folder, such as the `constants.py` file which has global variables defining things like the window size and FPS, and the `tileset.py` file which handles loading and rendering the tileset.

The `src/scenes` folder holds code related to the scene manager. `scene.py` contains an abstract class for creating new scenes and an enum class of all possible scenes. The menu, credits, and game scenes all inherit it, and you can find more details in the code docs.

The `game.py` scene script is the entry point to the actual game loop and gameplay. Releated code for the platformer, like level loading, mechanics, and entities will be located in the `src/game` folder, or we can have it in separate folders like `src/levels` and `src/entities` and so on.

The `assets` folder hold any resources like tileset, audio, fonts, and data files.