import sys
import PIL.Image
import pygame

class Room():
    def __init__(self,tilecolor):
        self.tiles = []
        self.tiletype = tilecolor
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
                
        width = (maxX - minX)
        height = (maxY - minY)

        self.surf = pygame.Surface((width*8, height*8))

        #TODO: then blit the required tile appearances onto the tiles according to their 'hasRight', 'hasLeft', etc combinations.

class Tile():
    def __init__(self,x,y):
        self.x = x
        self.y = y
        # and the following are for determining the visual appearance of this tile
        self.hasLeft = False
        self.hasRight = False
        self.hasUp = False
        self.hasDown = False

def colorsMatchAndAlphaIsNot128(c0,c1):
    if c0[0] == c1[0] and c0[1] == c1[1] and c0[2] == c1[2] and not c1[3] == 128:
        return True
    return False

def recursivelyFindNeighbouringPixelsOfSameColourAndAddToRoom(image,room,x,y):
    color = image.getpixel((x,y))
    image.putpixel((x,y),(color[0],color[1],color[2],128))
    t = Tile(x,y)
    room.tiles.append(t)

    if x-1 >= 0:    #check to left
        potential = image.getpixel((x-1,y))
        if colorsMatchAndAlphaIsNot128(color,potential):    #make sure it matches the colour and has not yet been processed
            t.hasLeft = True
            recursivelyFindNeighbouringPixelsOfSameColourAndAddToRoom(image,room,x-1,y)

    if x+1 < image.width:    #check to right
        potential = image.getpixel((x+1,y))
        if colorsMatchAndAlphaIsNot128(color,potential):    #make sure it matches the colour and has not yet been processed
            t.hasRight = True
            recursivelyFindNeighbouringPixelsOfSameColourAndAddToRoom(image,room,x+1,y)

    if y-1 >= 0:    #check above
        potential = image.getpixel((x,y-1))
        if colorsMatchAndAlphaIsNot128(color,potential):    #make sure it matches the colour and has not yet been processed
            t.hasUp = True
            recursivelyFindNeighbouringPixelsOfSameColourAndAddToRoom(image,room,x,y-1)

    if y+1 < image.height:    #check below
        potential = image.getpixel((x,y+1))
        if colorsMatchAndAlphaIsNot128(color,potential):    #make sure it matches the colour and has not yet been processed
            t.hasDown = True
            recursivelyFindNeighbouringPixelsOfSameColourAndAddToRoom(image,room,x,y+1)

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
            recursivelyFindNeighbouringPixelsOfSameColourAndAddToRoom(ship,newRoom,x,y)
            rooms.append(newRoom)

    # We now have a list of rooms where each room contains a bunch of tile coordinates, as well as the room's colour, which corresponds to the room's intended tileset

    return rooms