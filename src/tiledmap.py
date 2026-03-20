"""
Temporary file for testing
"""
import xml.etree.ElementTree as ET

class TiledMap:
    def __init__(self, file: str):
        self._file = file
        self.layers: dict[str, list[list[int]]] = {}
        self.width = 0
        self.height = 0

        self._load()

    def _load(self):
        root = ET.parse(self._file).getroot()
        self.width = int(root.attrib["width"])
        self.height = int(root.attrib["height"])

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
                map_data[y][x] = int(row[x])

        return map_data

    def get_tile(self, x: int, y: int, layer: str) -> int:
        """Get a single tile id from a layer"""
        return self.layers[layer][y][x]
