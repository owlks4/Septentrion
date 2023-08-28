import numpy
from pymunk import Vec2d

def rotatePosAroundPivot(p,pivot,angle):
    sin = numpy.sin(numpy.radians(angle))
    cos = numpy.cos(numpy.radians(angle))

    p = Vec2d(p.x + pivot.x, p.y + pivot.y)
    
    xnew = (p.x * cos) - (p.y * sin)
    ynew = (p.x * sin) + (p.y * cos)
    
    return Vec2d(xnew, ynew)