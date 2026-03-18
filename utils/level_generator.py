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
    NONE = [(0, 0, 0), 0]
    TILE = [(255, 255, 255), 1]
    RAMP_RIGHT = [(0, 0, 255), 3]
    RAMP_LEFT = [(255, 0, 0), 2]

def read_surface(surface: pygame.Surface, file_name: str):
    width = surface.width
    height = surface.height
    
    surface.lock()
    with open(f"{file_name}.txt", "w", encoding="") as file:
        file.write(f"{width} {height}\n")
        for y in range(0, height):
            for x in range(0, width):
                color = surface.get_at((x, y))
                color = (color.r, color.g, color.b)

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