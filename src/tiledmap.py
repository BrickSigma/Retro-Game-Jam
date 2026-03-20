"""
Temporary file for testing
"""
import xml.etree.ElementTree as ET
import pygame

import src.tileset as Tileset
from src.camera import Camera

type Tiles = list[list[int]]

class TiledMap:
    def __init__(self, file: str):
        self._file = file
        self.layers: dict[str, Tiles] = {}
        self.width = 0
        self.height = 0
        self.tile_size = 0

        # We're going to prerender the entire map onto a surface.
        # It'll use a little more memory, but will be faster to work with when rendering
        self._prerenders: dict[str, pygame.Surface] = {}

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
                self._prerender_map(child.attrib["name"])

    def _prerender_map(self, layer):
        self._prerenders[layer] = pygame.Surface((self.width*self.tile_size, self.height*self.tile_size), pygame.SRCALPHA)
        self._prerenders[layer].convert_alpha()

        for h in range(0, self.height):
            for w in range(0, self.width):
                tile_id = self.get_tile(w, h, layer)
                if tile_id == -1:
                    continue

                self._prerenders[layer].blit(Tileset.get_tile(tile_id), (w*self.tile_size, h*self.tile_size))

    def _parse_data(self, data:str) -> Tiles:
        map = data.split("\n")
        map_data: Tiles = []
        map.pop(0)
        map.pop()
        for y in range(0, self.height):
            map_data.append([-1]*self.width)
            row = map[y].split(",")
            for x in range(0, self.width):
                map_data[y][x] = int(row[x])-1  # We need to subtract 1 from the ID

        return map_data
    
    def get_tiles(self, layer: str) -> Tiles:
        """Get the tile data for a layer"""
        tiles = self.layers[layer]
        if tiles == None:
            raise Exception(f"{layer} does not exist!")
        return tiles

    def coord_in_map(self, x, y) -> bool:
        """Tests whether a point is in the tile map"""
        return (x < 0 or x >= self.width or y < 0 or y >= self.height)

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
        surface.blit(self._prerenders[layer], (-camera_pos[0], -camera_pos[1]))

    def get_tiles_rect(self, rect: pygame.Rect, layer: str) -> Tiles:
        """
        Return a region of the tile map. 
        This is useful for tile collision detection.

        `rect`: should be a tuple with (x, y, w, h) values
        """

        tiles = []
        for y in range(0, rect.h):
            tiles.append([-1]*rect.w)
            for x in range(0, rect.w):
                tile_x = x + rect.x
                tile_y = y + rect.y
                tile_id = self.get_tile(tile_x, tile_y, layer)
                tiles[y][x] = tile_id

        return tiles                
