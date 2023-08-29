import numpy
import pygame
import pymunk.pygame_util
import pymunk
from pymunk import Vec2d
import mapgenerator
import renderhelper
import globalVars
import pyglet
from pyglet.window import key
from pyglet.gl import glTranslatef  
from pyglet.gl import glRotatef
import pymunk.pyglet_util

rooms = []
sceneObjects = []

space = pymunk.Space()
space.gravity = Vec2d(0,-globalVars.GRAVITY_G)

#add the ground
ground = pymunk.Segment(space.static_body, Vec2d(0, globalVars.SCREEN_HEIGHT*0.2), Vec2d(globalVars.SCREEN_WIDTH, globalVars.SCREEN_HEIGHT*0.2), 1.0)
ground.friction = 0.5
ground.filter = pymunk.ShapeFilter(0,0b01,0b10)
space.add(ground)

draw_options = pymunk.pyglet_util.DrawOptions()

player_collision_filter = pymunk.ShapeFilter(0,0b10,0b01)

running = True

movementVector = Vec2d(0,0)

speedForMovement = 4000

currentVeh = 0

keys = None

spritesBatch = pyglet.graphics.Batch()

def movement():
    global movementVector, speedForMovement

    if keys[key.LEFT]:
        movementVector = Vec2d(-speedForMovement,movementVector.y)
    elif keys[key.RIGHT]:
        movementVector = Vec2d(speedForMovement,movementVector.y)
    else:
        movementVector = Vec2d(0,movementVector.y)

    if keys[key.I]:
        globalVars.translateCameraPosition(Vec2d(0,10))
    if keys[key.K]:
        globalVars.translateCameraPosition(Vec2d(0,-10))
    if keys[key.J]:
        globalVars.translateCameraPosition(Vec2d(-10,0))
    if keys[key.L]:
        globalVars.translateCameraPosition(Vec2d(10,0))
    if keys[key.A]:
        globalVars.rotateCamera(-10)
    if keys[key.D]:
        globalVars.rotateCamera(10)
    if keys[key.S]:
        globalVars.setCameraRotation(45)
        
def putObjectBehindOtherObjectInDrawList(object, other):
    sceneObjects.remove(object)
    sceneObjects.insert(sceneObjects.index(other),object) 

def getVerticesForRect(rect):
    return [[rect[0],rect[1]],[rect[2],rect[1]],[rect[2],rect[3]],[rect[0],rect[3]]]
    
def limitedVelocityFunc(body, gravity, damping, dt):
    pymunk.Body.update_velocity(body, space.gravity, 0.999, dt)  #then reset to regular gravity
    magnitude = body.velocity.length
                
    body.angular_velocity = 0   #Angular velocity is set to 0 here. Temporarily? We certainly don't want the player to be able to have angular velocity, but other objects (like boxes etc) might be able to.

    if magnitude > globalVars.MAX_VELOCITY:    #and also take this opportunity to limit our velocity to the max velocity
        scale = globalVars.MAX_VELOCITY / magnitude
        body.velocity = body.velocity * scale
                
    absAngularVelocity = numpy.abs(body.angular_velocity)
    if absAngularVelocity > globalVars.MAX_ANGULAR_VELOCITY:
        scale = globalVars.MAX_ANGULAR_VELOCITY/absAngularVelocity
        body.angular_velocity = body.angular_velocity * scale

class StaticSprite(pygame.sprite.Sprite):
    def __init__(self,spawnX,spawnY,imgPath):
        sceneObjects.append(self)
        global space
        super(StaticSprite, self).__init__()
        self.angle = 0
        image = pyglet.image.load(imgPath+".png")
        self.sprite = pyglet.sprite.Sprite(image, batch=spritesBatch,x=spawnX,y=spawnY)
        self.sprite.scale = globalVars.SPRITE_SCALE_FACTOR

    def update(self):
        return

class PhysicsObject(pygame.sprite.Sprite):
    def __init__(self,spawnX,spawnY,imgPath):
        sceneObjects.append(self)
        global space
        super(PhysicsObject, self).__init__()

        image = pyglet.image.load(imgPath+".png")
        self.sprite = pyglet.sprite.Sprite(image, batch=spritesBatch,x=spawnX,y=spawnY)
        self.sprite.scale = globalVars.SPRITE_SCALE_FACTOR
        self.sprite.rotation = 0
        self.rect = [0,0,self.sprite.width,self.sprite.height]

        self.body = None
        self.body = pymunk.Body()
        self.body.velocity_func = limitedVelocityFunc
        
        mass = 52
        friction = 0.5

        poly = pymunk.Poly(self.body,getVerticesForRect(self.rect))
        poly.mass = mass
        poly.friction = friction
        poly.filter = player_collision_filter
            
        space.add(self.body,poly)      
            
        self.body.position = spawnX,spawnY
    
    def update(self):
        global movementVector
        self.sprite.x = numpy.round(self.body.position.x)
        self.sprite.y = numpy.round(self.body.position.y)

        resistCameraRotationVisually = True
        if resistCameraRotationVisually:
            self.sprite.rotation = globalVars.cameraRotation
            self.body.angle = -numpy.radians(globalVars.cameraRotation)

        if self == currentVeh:
            if not (movementVector.x == 0 and movementVector.y == 0):
                self.body.apply_force_at_world_point(movementVector,self.body.local_to_world((0,0)))

music = pyglet.resource.media('assets/music/CalmBeforeTheStorm.mp3')
music.play()

rooms = mapgenerator.loadTilemap("./assets/shiplayout.png")
for room in rooms:
    room.makeSurface()

bgtest = StaticSprite(300,400,"./assets/bg")

veh = PhysicsObject(200,400,"./assets/capris")

currentVeh = veh

otherVeh = PhysicsObject(400,400,"./assets/capris")

def update(dt):
    movement()
    space.step(dt*2)

    for sprite in sceneObjects:
        sprite.update()

    camRotationRad = numpy.radians(-globalVars.cameraRotation)
    space.gravity = -globalVars.GRAVITY_G * Vec2d(-numpy.sin(camRotationRad), numpy.cos(camRotationRad))    #align the gravity downwards relative to the camera's rotation

    globalVars.setCameraPosition(Vec2d(-veh.sprite.x+globalVars.SCREEN_WIDTH/2,-veh.sprite.y+globalVars.SCREEN_HEIGHT/2))

globalVars.screen = pyglet.window.Window(width=globalVars.SCREEN_WIDTH, height=globalVars.SCREEN_HEIGHT, caption='Septentrion',vsync=True)

@globalVars.screen.event
def on_draw():
    globalVars.screen.clear()
    mapgenerator.backgroundBatch.draw()
   
    if globalVars.PHYSICS_DEBUG_DRAW:
        space.debug_draw(draw_options)

    spritesBatch.draw()

keys = key.KeyStateHandler()
globalVars.screen.push_handlers(keys)
pyglet.clock.schedule_interval(update,1/(globalVars.FRAME_RATE))
pyglet.app.run()