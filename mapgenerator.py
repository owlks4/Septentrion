import sys
import PIL.Image
from enum import IntEnum
import globalVars
import pyglet

class TileType(IntEnum):
    CENTRE = 0
    LEFT_WALL = 1
    RIGHT_WALL = 2
    CEILING = 3
    FLOOR = 4
    CEILING_TRIM = 5
    FLOOR_TRIM = 6

GLOBAL_SPRITE_SCALE_FACTOR = 0  #this gets set by main.py fairly immediately; it's only duplicated here to avoid a circular reference
screen = None #this gets set by main.py fairly immediately; it's only duplicated here to avoid a circular reference
backgroundBatch = pyglet.graphics.Batch()

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

        for tile in self.tiles:
            image_part = self.tileset.tiles[tile.tileType]         
            pasteArea = (((tile.x*8*globalVars.SPRITE_SCALE_FACTOR)+globalVars.SCREEN_WIDTH/2), (tile.y*8*globalVars.SPRITE_SCALE_FACTOR)+globalVars.SCREEN_HEIGHT/2)
            tile.sprite = pyglet.sprite.Sprite(image_part, batch=backgroundBatch,x=pasteArea[0],y=pasteArea[1])
            tile.sprite.scale = globalVars.SPRITE_SCALE_FACTOR
            tile.image = None

    def evaluateMotion(self):
        return

class Tile():
    def __init__(self,x,y,tileType):    #TileType: controlled by the green channel.
        self.x = x
        self.y = y
        self.tileType = TileType(tileType)

class Tileset():
    def __init__(self,path):
        image = pyglet.image.load(path)
        self.tiles = []
        for tileType in TileType:
            cropArea = self.getCropAreaForTileType(tileType)
            self.tiles.append(image.get_region(x=cropArea[0], y=cropArea[1], width=cropArea[2], height=cropArea[3]))
    
    def getCropAreaForTileType(self,tileType):
        match tileType:
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
                return (24,8,8,8)
            case TileType.FLOOR_TRIM:
                return (24,16,8,8)
            case _:
                print("Instructions for cutting the tileType "+str(tileType) +" from the tileset were not found!")

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