import sys
import PIL.Image
import pygame
from pygame import Surface
from enum import Enum
import numpy
import renderhelper
import globalVars
from pymunk import Vec2d

class TileType(Enum):
    CENTRE = 0
    LEFT_WALL = 1
    RIGHT_WALL = 2
    CEILING = 3
    FLOOR = 4
    CEILING_TRIM = 5
    FLOOR_TRIM = 6

GLOBAL_SPRITE_SCALE_FACTOR = 0  #this gets set by main.py fairly immediately; it's only duplicated here to avoid a circular reference
screen = None #this gets set by main.py fairly immediately; it's only duplicated here to avoid a circular reference

class Room():
    def __init__(self,tilecolor):
        self.tiles = []
        self.tileset = Tileset("./assets/tilesets/"+str(tilecolor[0])+".png")
    def makeSurface(self):
        minX = minY = sys.maxsize
        maxX = maxY = -sys.maxsize

        for tile in self.tiles:
            if tile.x < minX:
                minX = tile.x
            if tile.x > maxX:
                maxX = tile.x
            if tile.y < minY:
                minY = tile.y
            if tile.y > maxY:
                maxY = tile.y

        self.x = minX * 8 * globalVars.SPRITE_SCALE_FACTOR
        self.y = minY * 8 * globalVars.SPRITE_SCALE_FACTOR

        width = (maxX - minX) + 1       #The +1 is because it's only looking at the topleftmost corners of tiles; if we didn't add 1, the tiles along the right and the bottom would be missed out, because the room rect would only have reached their origin, rather than having encompassed their extents
        height = (maxY - minY) + 1

        self.surfUnrotated = Surface((width*8, height*8)).convert_alpha()

        for tile in self.tiles:
            self.surfUnrotated.blit(self.tileset.image, ((tile.x - minX)*8, (tile.y-minY)*8), self.tileset.getCropAreaForTileType(tile))

        self.surfUnrotated = pygame.transform.scale_by(self.surfUnrotated,globalVars.SPRITE_SCALE_FACTOR)

        self.testOffsetX = 0

    def draw(self):
        self.surf = pygame.transform.rotate(self.surfUnrotated, -globalVars.cameraRotation)        

        p = Vec2d(self.x, self.y)

        p = renderhelper.rotatePosAroundPivot(p, globalVars.cameraPosition, globalVars.cameraRotation)   #rotate position around camera pivot, to account for camera rotation

        diffX = 0
        diffY = 0

        angle_rads = numpy.radians(-globalVars.cameraRotation)
                                               
        if globalVars.cameraRotation > 0 and globalVars.cameraRotation <= 90:
            diffX = numpy.sin(-angle_rads) * self.surfUnrotated.get_size()[1] # WORKS! DON'T TOUCH IT! # half the difference between the width of the unrotated and the width of the rotated, i.e. the width across the sloped part that has been created
        elif globalVars.cameraRotation >= 90 and -globalVars.cameraRotation <= 180:
            diffX = numpy.sin(-angle_rads) * self.surfUnrotated.get_size()[1] - numpy.cos(angle_rads) * self.surfUnrotated.get_size()[0] 
            diffY = numpy.sin(numpy.radians(globalVars.cameraRotation - 90)) * self.surfUnrotated.get_size()[1]
        elif globalVars.cameraRotation <= -90 and globalVars.cameraRotation >= -180:
            diffX = numpy.cos(numpy.radians(180-globalVars.cameraRotation)) * self.surfUnrotated.get_size()[0] 
            diffY = -numpy.sin(angle_rads + numpy.radians(90)) * self.surfUnrotated.get_size()[1] - numpy.sin(angle_rads + numpy.radians(180)) * self.surfUnrotated.get_size()[0]
        elif globalVars.cameraRotation <= 0 and globalVars.cameraRotation > -90:
            diffY = numpy.sin(angle_rads) * self.surfUnrotated.get_size()[0]

        offset = Vec2d(diffX,diffY)
        p = p - offset

        globalVars.screen.blit(self.surf, (round((p.x)+globalVars.SCREEN_WIDTH/2), round(p.y+globalVars.SCREEN_HEIGHT/2)))

    def evaluateMotion(self):
        return

class Tile():
    def __init__(self,x,y,tileType):    #TileType: controlled by the green channel.
        self.x = x
        self.y = y
        self.tileType = TileType(tileType)

class Tileset():
    def __init__(self,path):
        self.image = pygame.image.load(path)
    
    def getCropAreaForTileType(self,tile):
        match tile.tileType:
            case TileType.CENTRE:
                return (8,8,8,8)
            case TileType.LEFT_WALL: 
                return (16,8,8,8)
            case TileType.RIGHT_WALL:
                return (0,8,8,8)
            case TileType.CEILING:
                return (8,16,8,8)
            case TileType.FLOOR:
                return (8,0,8,8)
            case TileType.CEILING_TRIM:
                return (24,0,8,8)
            case TileType.FLOOR_TRIM:
                return (24,8,8,8)
            case _:
                print("Instructions for cutting the tileType "+str(tile.tileType) +" from the tileset were not found!")

def recursivelyFindNeighbouringPixelsWithSameRedChannelAndAddToRoom(image,room,x,y):
    color = image.getpixel((x,y))
    image.putpixel((x,y),(color[0],color[1],color[2],128))
    t = Tile(x,y,color[2])

    if x-1 >= 0:    #check to left
        potential = image.getpixel((x-1,y))
        if color[0] == potential[0] and not color[3] == 128:    #make sure the red channel matches, and that the pixel has not yet been processed
            recursivelyFindNeighbouringPixelsWithSameRedChannelAndAddToRoom(image,room,x-1,y)

    if x+1 < image.width:    #check to right
        potential = image.getpixel((x+1,y))
        if color[0] == potential[0] and not color[3] == 128:    #make sure the red channel matches, and that the pixel has not yet been processed
            recursivelyFindNeighbouringPixelsWithSameRedChannelAndAddToRoom(image,room,x+1,y)

    if y-1 >= 0:    #check above
        potential = image.getpixel((x,y-1))
        if color[0] == potential[0] and not color[3] == 128:    #make sure the red channel matches, and that the pixel has not yet been processed
            recursivelyFindNeighbouringPixelsWithSameRedChannelAndAddToRoom(image,room,x,y-1)

    if y+1 < image.height:    #check below
        potential = image.getpixel((x,y+1))
        if color[0] == potential[0] and not color[3] == 128:    #make sure the red channel matches, and that the pixel has not yet been processed
            recursivelyFindNeighbouringPixelsWithSameRedChannelAndAddToRoom(image,room,x,y+1)

    room.tiles.append(t)

def colToHex(rgbTuple):
    tupleWithoutAlpha = (rgbTuple[0],rgbTuple[1],rgbTuple[2])
    return '#%02x%02x%02x' % tupleWithoutAlpha

def loadTilemap(path):
    ship = PIL.Image.open(path)
    ship.putalpha(255)                  #set all alpha values to 255
    rooms = []

    for x in range(ship.width):    
        for y in range(ship.height):
            pixelColor = ship.getpixel((x,y))
            if pixelColor[0] == 0 and pixelColor[1] == 0 and pixelColor[2] == 0:   #pure black pixels form the extraneous space around the ship, and are not counted
                continue
            if pixelColor[3] == 128:     #if the alpha value of the pixel was 128, it means we already checked it in a previous loop, and that it's already forming part of a room - so no need to check it
                continue
            newRoom = Room(pixelColor)
            recursivelyFindNeighbouringPixelsWithSameRedChannelAndAddToRoom(ship,newRoom,x,y)
            rooms.append(newRoom)

    # We now have a list of rooms where each room contains a bunch of tile coordinates, as well as the room's colour, which corresponds to the room's intended tileset

    return rooms