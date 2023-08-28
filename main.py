import numpy
import pygame
import pymunk.pygame_util
import pymunk
from pymunk import Vec2d
import mapgenerator
from mapgenerator import Room

pygame.init()

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
PHYSICS_DEBUG_DRAW = False
FRAME_RATE = 60
MAX_VELOCITY = 144
MAX_ANGULAR_VELOCITY = 1
GRAVITY_G = 9.81
GLOBAL_SPRITE_SCALE_FACTOR = 3
mapgenerator.GLOBAL_SPRITE_SCALE_FACTOR = GLOBAL_SPRITE_SCALE_FACTOR

cameraPosition = Vec2d(0,0)
cameraRotation = 0

rooms = []
sceneObjects = []

screen = pygame.display.set_mode([SCREEN_WIDTH, SCREEN_HEIGHT])
pygame.display.set_caption("Septentrion")
space = pymunk.Space()
space.gravity = Vec2d(0,GRAVITY_G)
draw_options = pymunk.pygame_util.DrawOptions(screen)

#add the ground
ground = pymunk.Segment(space.static_body, Vec2d(0, SCREEN_HEIGHT*0.8), Vec2d(SCREEN_WIDTH, SCREEN_HEIGHT*0.8), 1.0)
ground.friction = 0.5
ground.filter = pymunk.ShapeFilter(0,0b01,0b10)
space.add(ground)

player_collision_filter = pymunk.ShapeFilter(0,0b10,0b01)

lastFrameWasAt = 0
lastFrameDuration = 0
nanosecondsPerFrame = 1000000000 / FRAME_RATE

running = True

right = left = a = d = spacebar = False

movementVector = Vec2d(0,0)
turnAmount = 0

speedForMovement = 400
speedForTurn = 2500

currentVeh = 0

def updateMovementVector():
    global up,down,left,right,speedForMovement,movementVector,turnAmount,speedForTurn,a,d,spacebar
    
    x = movementVector.x
    y = movementVector.y

    if right:
        x = speedForMovement
    elif left:
        x = -speedForMovement
    else:
        x = 0

    if a:
        turnAmount = -speedForTurn
    elif d:
        turnAmount = speedForTurn
    else:
        turnAmount = 0

    movementVector = Vec2d(x,y)

def checkEvents():
    global up,right,down,left,running,a,d,spacebar,cameraRotation
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            match event.key:
                case pygame.K_RIGHT:
                    right = True
                case pygame.K_LEFT:
                    left = True 
                case pygame.K_a:
                    a = True  
                case pygame.K_d:
                    d = True  
                    cameraRotation += 10
                case pygame.K_SPACE:
                    spacebar = True;
                    currentVeh.body.apply_impulse_at_local_point(-space.gravity*200,(0,0))
                   
        elif event.type == pygame.KEYUP:
            match event.key:
                case pygame.K_RIGHT:
                    right = False
                case pygame.K_LEFT:
                    left = False
                case pygame.K_a:
                    a = False  
                case pygame.K_d:
                    d = False   
                case pygame.K_SPACE:
                    spacebar = False

        updateMovementVector()

def rotatePosAroundPivot(p,pivot,angle):
    sin = numpy.sin(numpy.radians(angle))
    cos = numpy.cos(numpy.radians(angle))

    p = Vec2d(p.x + pivot.x, p.y + pivot.y)
    
    xnew = (p.x * cos) - (p.y * sin)
    ynew = (p.x * sin) + (p.y * cos)
    
    return Vec2d(xnew, ynew)     
  
def putObjectBehindOtherObjectInDrawList(object, other):
    sceneObjects.remove(object)
    sceneObjects.insert(sceneObjects.index(other),object) 

def getVerticesForRect(rect):
    w = rect[2] - rect[0]
    h = rect[3] - rect[1]
    
    rect[0] -= w/2
    rect[2] -= w/2
    rect[1] -= h/2
    rect[3] -= h/2
    
    return [[rect[0],rect[1]],[rect[2],rect[1]],[rect[2],rect[3]],[rect[0],rect[3]]]
    
def limitedVelocityFunc(body, gravity, damping, dt):
    pymunk.Body.update_velocity(body, space.gravity, 0.999, dt)  #then reset to regular gravity
    magnitude = body.velocity.length
    magnitude = body.velocity.length
                
    body.angular_velocity = 0   #Angular velocity is set to 0 here. Temporarily? We certainly don't want the player to be able to have angular velocity, but other objects (like boxes etc) might be able to.

    if magnitude > MAX_VELOCITY:    #and also take this opportunity to limit our velocity to the max velocity
        scale = MAX_VELOCITY / magnitude
        body.velocity = body.velocity * scale
                
    absAngularVelocity = numpy.abs(body.angular_velocity)
    if absAngularVelocity > MAX_ANGULAR_VELOCITY:
        scale = MAX_ANGULAR_VELOCITY/absAngularVelocity
        body.angular_velocity = body.angular_velocity * scale

class StaticSprite(pygame.sprite.Sprite):
    def __init__(self,spawnX,spawnY,imgPath):
        sceneObjects.append(self)
        global space
        super(StaticSprite, self).__init__()
        self.angle = 0
        self.surfUnrotated = pygame.transform.scale_by(pygame.image.load(imgPath+".png").convert_alpha(), GLOBAL_SPRITE_SCALE_FACTOR);    
        self.surf = self.surfUnrotated        
        self.rect = self.surf.get_rect()
        self.position = Vec2d(spawnX,spawnY)
    
    def draw(self):
        resistCameraRotationVisually = False

        angle_degrees = numpy.degrees(-self.angle)
        
        if not resistCameraRotationVisually:
            angle_degrees -= cameraRotation
            self.surf = pygame.transform.rotate(self.surfUnrotated, angle_degrees)        

        p = Vec2d(self.position.x, self.position.y)

        p = rotatePosAroundPivot(p,cameraPosition,cameraRotation)   #rotate position around camera pivot, to account for camera rotation

        offset = Vec2d(*self.surf.get_size()) / 2
        p = p - offset

        screen.blit(self.surf, (round(p.x+SCREEN_WIDTH/2), round(p.y+SCREEN_HEIGHT/2)))

    def evaluateMotion(self):
        return  #This will get called, but only does anything on physics objects. But could be used to make it evaluate animation?

class PhysicsObject(pygame.sprite.Sprite):
    def __init__(self,spawnX,spawnY,imgPath):
        sceneObjects.append(self)
        global space
        super(PhysicsObject, self).__init__()
        self.angle = 0
        self.surfUnrotated = pygame.transform.scale_by(pygame.image.load(imgPath+".png").convert_alpha(), GLOBAL_SPRITE_SCALE_FACTOR);    
        self.surf = self.surfUnrotated        
        self.rect = self.surf.get_rect()
        self.body = None
        self.body = pymunk.Body()
        self.body.velocity_func = limitedVelocityFunc
        
        mass = 52
        friction = 1

        poly = pymunk.Poly(self.body,getVerticesForRect(self.rect))
        poly.mass = mass
        poly.friction = friction
        poly.filter = player_collision_filter
            
        space.add(self.body,poly)      
            
        self.body.position = spawnX,spawnY

        self.rect = self.surf.get_rect()
        self.body.center_of_gravity = (self.rect.x / 2, self.rect.y/2)
    
    def draw(self):
        resistCameraRotationVisually = True

        angle_degrees = numpy.degrees(-self.body.angle)
        
        if not resistCameraRotationVisually:
            angle_degrees -= cameraRotation
            self.surf = pygame.transform.rotate(self.surfUnrotated, angle_degrees)        

        p = Vec2d(self.body.position.x, self.body.position.y)

        p = rotatePosAroundPivot(p,cameraPosition,cameraRotation)   #rotate position around camera pivot, to account for camera rotation

        offset = Vec2d(*self.surf.get_size()) / 2
        p = p - offset

        screen.blit(self.surf, (round(p.x+SCREEN_WIDTH/2), round(p.y+SCREEN_HEIGHT/2)))

    def evaluateMotion(self):
        global movementVector

        if self == currentVeh:
            if not (movementVector.x == 0 and movementVector.y == 0):
                self.body.apply_force_at_world_point(movementVector,self.body.local_to_world((0,0)))
                self.body.torque = movementVector.x*1.1

            if not turnAmount == 0:
                self.body.torque = turnAmount

pygame.mixer.music.load('./assets/music/TheSinkingShip.mp3')
pygame.mixer.music.play(-1)

rooms = mapgenerator.loadTilemap("./assets/shiplayout.png")
rooms[0].makeSurface()
rooms[0].surf = pygame.transform.scale_by(rooms[0].surf,GLOBAL_SPRITE_SCALE_FACTOR)

rooms[1].makeSurface()
rooms[1].surf = pygame.transform.scale_by(rooms[1].surf,GLOBAL_SPRITE_SCALE_FACTOR)


bgtest = StaticSprite(300,550,"./assets/bg")

veh = PhysicsObject(200,524,"./assets/capris")

currentVeh = veh

otherVeh = PhysicsObject(400,550,"./assets/capris")


while running:
    checkEvents()

    cameraPosition=Vec2d(-veh.body.position.x,-veh.body.position.y)

    draw_options.transform = (
        pymunk.Transform.translation(cameraPosition.x, cameraPosition.y)        #these debug physics draws do not currently sync with camera rotation!
        @ pymunk.Transform.translation(SCREEN_WIDTH/2, SCREEN_HEIGHT/2)
        )

    camRotationRad = numpy.radians(-cameraRotation)
    space.gravity = GRAVITY_G * Vec2d(-numpy.sin(camRotationRad), numpy.cos(camRotationRad))    #align the gravity downwards relative to the camera's rotation
    space.step(1/FRAME_RATE)

    screen.fill("skyblue")

    posForCircle = Vec2d(700,200)
    posForCircle = rotatePosAroundPivot(posForCircle,cameraPosition,cameraRotation)
    posForCircle = Vec2d(posForCircle.x+SCREEN_WIDTH/2,posForCircle.y+SCREEN_HEIGHT/2)
    pygame.draw.circle(screen,"yellow",posForCircle,100)

    posForCircle = Vec2d(200,300)
    posForCircle = rotatePosAroundPivot(posForCircle,cameraPosition,cameraRotation)
    posForCircle = Vec2d(posForCircle.x+SCREEN_WIDTH/2,posForCircle.y+SCREEN_HEIGHT/2)
    pygame.draw.circle(screen,"red",posForCircle,50)

    screen.blit(rooms[0].surf, (round(rooms[0].x + SCREEN_WIDTH/2), round(rooms[0].y + SCREEN_HEIGHT/2)))
    screen.blit(rooms[1].surf, (round(rooms[1].x + SCREEN_WIDTH/2), round(rooms[1].y + SCREEN_HEIGHT/2)))

    #pygame.draw.rect(screen,"forestgreen",[0+cameraPosition.x,555+cameraPosition.y,1280,720])
        
    if PHYSICS_DEBUG_DRAW:
        space.debug_draw(draw_options)
    
    for sprite in sceneObjects:
        sprite.evaluateMotion()
        sprite.draw()

    pygame.display.flip()
    
pygame.quit()