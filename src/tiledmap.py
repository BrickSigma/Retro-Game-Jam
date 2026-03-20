"""
Temporary file for testing
"""
import xml.etree.ElementTree as ET
import pygame

import src.tileset as Tileset
from src.camera import Camera

class TiledMap:
    def __init__(self, file: str):
        self._file = file
        self.layers: dict[str, list[list[int]]] = {}
        self.width = 0
        self.height = 0
        self.tile_size = 0

        self._load()

    def _load(self):
        root = ET.parse(self._file).getroot()
        self.width = int(root.attrib["width"])
        self.height = int(root.attrib["height"])
        self.tile_size = int(root.attrib["tilewidth"])

        for child in root:
            if child.tag == "layer":
                data = child.find("data").text
                map_data = self._parse_data(data)
                self.layers[child.attrib["name"]] = map_data

    def _parse_data(self, data:str) -> list[list[int]]:
        map = data.split("\n")
        map_data: list[list[int]] = []
        map.pop(0)
        map.pop()
        for y in range(0, self.height):
            map_data.append([0]*self.width)
            row = map[y].split(",")
            for x in range(0, self.width):
                map_data[y][x] = int(row[x])-1  # We need to subtract 1 from the ID

        return map_data

    def get_tile(self, x: int, y: int, layer: str) -> int:
        """Get a single tile id from a layer"""
        if (x < 0 or x >= self.width or y < 0 or y >= self.height):
            return -1
        return self.layers[layer][y][x]
    
    def size(self) -> tuple[int, int]:
        """Return the level size"""
        return (self.width, self.height)
    
    def draw_layer(self, surface: pygame.Surface, camera: Camera, layer: str):
        camera_pos = camera.get_pos()
        camera_tile = [0, 0]
        camera_tile[0] = camera_pos[0]//self.tile_size
        camera_tile[1] = camera_pos[1]//self.tile_size
        
        camera_tile_pos = [camera_tile[0]*self.tile_size, camera_tile[1]*self.tile_size]
        camera_delta = [0, 0]
        camera_delta[0] = camera_pos[0] - camera_tile_pos[0]
        camera_delta[1] = camera_pos[1] - camera_tile_pos[1]
        
        for y in range(0, Camera.HEIGHT + 1):
            for x in range(0, Camera.WIDTH +1):
                tile_x = x + camera_tile[0]
                tile_y = y + camera_tile[1]
                tile_id = self.get_tile(tile_x, tile_y, layer)
                if tile_id == -1:
                    continue

                surface.blit(Tileset.get_tile(tile_id), (x*self.tile_size - camera_delta[0], y*self.tile_size - camera_delta[1]))