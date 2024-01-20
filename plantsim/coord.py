from __future__ import annotations
from pydantic import BaseModel

class Coord(BaseModel):
    x: int
    y: int

    def __init__(self, x: int, y: int):
        super(Coord, self).__init__(x=x, y=y)

    @property
    def xy(self) -> tuple[int, int]:
        return (self.x, self.y)
    
    def copy(self) -> Coord:
        return Coord(self.x, self.y)
    
    def __add__(self, other: Coord) -> Coord:
        return Coord(self.x + other.x, self.y + other.y)
    
    # def __iadd__(self, other: Coord) -> Coord:
    #     return Coord(self.x + other.x, self.y + other.y)
    
    # def __sub__(self, other: Coord) -> Coord:
    #     return Coord(self.x - other.x, self.y - other.y)
    
    def __neg__(self, other: Coord) -> Coord:
        return Coord(-self.x, -self.y)
    
    def __hash__(self):
        return hash(self.xy)

    def __eq__(self, other: Coord):
        return self.xy == other.xy 