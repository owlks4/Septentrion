from pymunk import Vec2d
import pygame

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
PHYSICS_DEBUG_DRAW = False
FRAME_RATE = 60
MAX_VELOCITY = 144
MAX_ANGULAR_VELOCITY = 1
GRAVITY_G = 9.81
SPRITE_SCALE_FACTOR = 3

cameraPosition = Vec2d(0,0)
cameraRotation = 0.0

screen = pygame.display.set_mode([SCREEN_WIDTH, SCREEN_HEIGHT])