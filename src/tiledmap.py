import xml.etree.ElementTree as ET
import pygame
import pytmx
from enum import Enum, auto

import src.tileset as Tileset
from src.camera import Camera
from src.tile import Tile, TileType
from src.entities.entity import *

type Tiles = list[list[Tile]]

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

        self.tmx = pytmx.load_pygame(file)
        self.get_entities()

        # I've kept the old parser as the tilemap still uses it, but rendering uses pytmx now
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
        """
        Old code for prerendering the map. I've kept in it for archive referencing incase performance drops
        """
        self._prerenders[layer] = pygame.Surface((self.width*self.tile_size, self.height*self.tile_size), pygame.SRCALPHA)
        self._prerenders[layer].convert_alpha()

        for h in range(0, self.height):
            for w in range(0, self.width):
                tile_id = self.get_tile(w, h, layer).type.value
                if tile_id == None:
                    continue

                self._prerenders[layer].blit(Tileset.get_tile(tile_id), (w*self.tile_size, h*self.tile_size))

    def _parse_data(self, data:str) -> Tiles:
        """
        This function sets up the tile collision maps
        """
        map = data.split("\n")
        map_data: Tiles = []
        map.pop(0)
        map.pop()
        for y in range(0, self.height):
            map_data.append([-1]*self.width)
            row = map[y].split(",")
            for x in range(0, self.width):
                value = int(row[x])-1
                if value == -1:
                    map_data[y][x] = Tile(x, y, TileType.NONE, False, False)
                    continue
                flip_x = bool(value & 0x80000000)
                flip_y = bool(value & 0x40000000)
                value &= 0x0000ffff
                map_data[y][x] = Tile(x, y, TileType(value), flip_x, flip_y)  # We need to subtract 1 from the ID

        return map_data
    
    def get_layer(self, layer: str):
        """
        Safely fetch a layer by name.
        Returns None instead of crashing if the layer doesn't exist.
        """
        try:
            return self.tmx.get_layer_by_name(layer)
        except ValueError:
            return None
    
    def get_layer_tiles(self, layer: str) -> Tiles:
        """
        Safely fetch a layer by name.
        Returns None instead of crashing if the layer doesn't exist.
        """
        try:
            return self.layers[layer]
        except:
            return None
    
    def get_tiles(self, layer: str) -> Tiles | None:
        """Get the tile data for a layer"""
        tiles = self.get_layer_tiles(layer)
        return tiles

    def get_tile(self, x: int, y: int, layer: str) -> Tile:
        """Get a single tile id from a layer"""
        if (x < 0 or x >= self.width or y < 0 or y >= self.height):
            return None
        return self.layers[layer][y][x]
    
    def size(self) -> tuple[int, int]:
        """Return the level size"""
        return (self.width, self.height)
    
    def draw_layer(self, surface: pygame.Surface, camera: Camera, layer: str, color_mask: tuple[int] = None):
        camera_pos = camera.get_pos()
        layer_data = self.get_layer(layer)
        if layer_data is None:
            return
        
        surf_mask = pygame.Surface(surface.size, pygame.SRCALPHA) if color_mask is not None else surface

        camera_pos = camera.get_pos()
        camera_tile_x = camera_pos[0] // self.tile_size
        camera_tile_y = camera_pos[1] // self.tile_size
        camera_delta_x = camera_pos[0] - camera_tile_x * self.tile_size
        camera_delta_y = camera_pos[1] - camera_tile_y * self.tile_size

        for x, y, gid in layer_data:
            if gid == 0:
                continue
            tile_image = self.tmx.get_tile_image_by_gid(gid)
            if tile_image is None:
                continue
            screen_x = (x - camera_tile_x) * self.tile_size - camera_delta_x
            screen_y = (y - camera_tile_y) * self.tile_size - camera_delta_y
            # Only draw tiles visible in the viewport
            if (-self.tile_size < screen_x < Camera.WIDTH * self.tile_size and
                    -self.tile_size < screen_y < Camera.HEIGHT * self.tile_size):
                surf_mask.blit(tile_image, (screen_x, screen_y))

        if color_mask is not None:
            surface.blit(Tileset.swap_color(surf_mask, (255, 255, 255), color_mask), (0, 0))

    def get_tiles_rect(self, rect: pygame.Rect, layer: str) -> Tiles:
        """
        Return a region of the tile map. 
        This is useful for tile collision detection.

        `rect`: should be a tuple with (x, y, w, h) values
        """

        tiles: list[list[Tile]] = []
        for y in range(0, rect.h):
            tiles.append([])
            for x in range(0, rect.w):
                tile_x = x + rect.x
                tile_y = y + rect.y
                tile = self.get_tile(tile_x, tile_y, layer)
                if tile == None:
                    tile = Tile(tile_x, tile_y, TileType.NONE, False, False)
                tiles[y].append(tile)

        return tiles           

    def get_entities(self) -> list[Entity]:
        entities: list[Entity] = []

        for entity in self.tmx.objects:
            type = EntityType.from_name(entity.type)
            match type:
                case EntityType.SPIKE:
                    entities.append(Spike(entity.x, entity.y, type, entity.rotation))
                case _:
                    entities.append(Entity(entity.x, entity.y, EntityType.from_name(entity.type)))

        return entities
    