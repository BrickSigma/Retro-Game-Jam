"""
This script is used for generating level text file sheets from PNGs.
"""
from enum import Enum, unique
import sys
import os
import pygame

pygame.init()

@unique
class TileColor(Enum):
    NONE = [(0, 0, 0), -1]
    ARROW = [None, 39]
    BRICK = [(255, 255, 255), 40]
    BROKEN_BRICK = [(0, 255, 0), 41]
    SOLID_BRICK = [(255, 0, 0), 42]
    CAVE_TOP_LEFT = [(255, 128, 0), 43]
    CAVE_TOP_RIGHT = [(255, 255, 0), 44]
    CAVE_BOTTOM_LEFT = [(128, 255, 0), 45]
    CAVE_BOTTOM_RIGHT = [(0, 255, 128), 46]
    CAVE_DETAIL = [(0, 0, 255), 47]
    CAVE_FLOOR = [(0, 255, 255), 48]
    CAVE_ROOF = [(0, 128, 255), 49]
    CAVE_WALL_LEFT = [(255, 0, 255), 50]
    CAVE_WALL_RIGHT = [(255, 0, 128), 51]
    RAMP_RIGHT = [(128, 0, 255), 52]
    RAMP_LEFT = [(128, 0, 128), 53]
    CAVE_CORNER_LEFT = [(200, 0, 100), 54]
    CAVE_CORNER_RIGHT = [(200, 0, 200), 55]
    PILLAR_TOP = [(96, 96, 96), 56]
    PILLAR_BOTTOM = [(32, 32, 32), 57]
    PILLAR_MIDDLE = [(64, 64, 64), 58]
    LADDER = [(100, 0, 0), 59]

def read_surface(surface: pygame.Surface, file_name: str):
    width = surface.width
    height = surface.height
    
    surface.lock()
    with open(f"{file_name}.txt", "w") as file:
        file.write(f"{width} {height}\n")
        for y in range(0, height):
            for x in range(0, width):
                color = surface.get_at((x, y))
                color = (color.r, color.g, color.b)
                if color == TileColor.NONE.value[0]:
                    file.write("-1,")
                    continue

                for tile in list(TileColor):
                    if color == tile.value[0]:
                        file.write(str(tile.value[1]))
                        break
                
                if x < (width - 1):
                    file.write(",")
                    
            file.write("\n")

    surface.unlock()


def main():
    if len(sys.argv) < 2:
        print("Invalid arguments!")
        return
    
    argv = sys.argv[1:]

    for file in argv:
        if not os.path.isfile(file):
            print(f"{file} does not exist!")
            return
        
    for file in argv:
        file_name, extension = os.path.splitext(file)
        if not extension == ".png":
            print(f"{file} is not a PNG!")
            continue

        surface = pygame.image.load(file)
        read_surface(surface, file_name)

    pygame.quit()


main()