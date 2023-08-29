from pymunk import Vec2d
import pygame
import pyglet

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
PHYSICS_DEBUG_DRAW = False
FRAME_RATE = 60.0
MAX_VELOCITY = 144
MAX_ANGULAR_VELOCITY = 1
GRAVITY_G = 9.81
SPRITE_SCALE_FACTOR = 3

cameraPosition = Vec2d(0,0)
cameraRotation = 0.0

pyglet.gl.glClearColor(0, 0, 0, 1.0)
pyglet.gl.glEnable(pyglet.gl.GL_DEPTH_TEST)
pyglet.gl.glEnable(pyglet.gl.GL_CULL_FACE)
pyglet.image.Texture.default_mag_filter = pyglet.image.GL_NEAREST

def translateCameraPosition(translation):
    global cameraPosition
    cameraPosition = Vec2d(cameraPosition.x + translation.x, cameraPosition.y + translation.y)