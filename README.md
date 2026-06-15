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

## A game is just one big **state machine**
I think this is an important point to note. If you go through the code, specifically the `scene.py`,`level.py`, and `stage.py` files you'll notice that each have an enum class that creates states. Everything in a game, such as moving from the menu screen to the game, or from level 1 to level 2, is just a state transition in one big automata, with little state machines nested in one another (such as stages being in levels, levels being in scenes, and so on...).

This concept helps with breaking down similar systems into groups, and managing them at smaller, easier to read sections. If you're having a bug with transitions between stages, take a look at the `level.py` file, if tile collisions isn't working, it's probably in the `stage.py` file.

Each class defines a state/node in the game. All classes have two functions always defined: 
```py
def __init__(self): ...
def update() -> State: ...
```
`__init__` will initialize the state to a default setting when it's entered from a different state, and `update` will run each frame the game is on the state. It should be noted that the depeest call to `update` will handle all events and rendering to the screen.

To build an executable, first install pyinstaller `pip install pyinstaller` then run the command `python -m PyInstaller Skyfall.spec`
