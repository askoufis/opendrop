from opendrop.utility.vectors import Vector2

class ResolutionTuple(Vector2):
    def __repr__(self):
        return "{0}({x}, {y})".format(self.__class__.__name__, x=self.x, y=self.y)

    def __str__(self):
        return "{x}px {y}px".format(x=self.x, y=self.y)
