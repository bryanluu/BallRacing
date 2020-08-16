import pygame
import os
from pygame.locals import *


# returns a number x if it falls within the bounds [lb, ub]
# otherwise returns the closest bound
def bound(lb, x, ub):
    return min(max(lb, x), ub)


# returns a number on a ramp with given start and end
# at progress frac (between 0 and 1)
def ramp(start, end, frac):
    frac = bound(0, frac, 1)
    return start * (1 - frac) + end * frac


# returns a number on a seesaw between lb and ub
# at progress frac (0 = lb, 0.5 = ub, 1 = lb)
def seesaw(lb, ub, frac):
    frac = bound(0, frac, 1)
    f = abs(frac - 0.5) / 0.5
    return lb * f + ub * (1 - f)


def load_image(name, colorkey=None):
    fullname = os.path.join('resources', name)
    try:
        image = pygame.image.load(fullname)
    except pygame.error as message:
        print('Cannot load image: {0}'.format(name))
        raise SystemExit(message)
    image = image.convert()
    if colorkey is not None:
        if colorkey is -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey, RLEACCEL)
    return image


def load_sound(name):
    class NoneSound:
        def play(self): pass
    if not pygame.mixer:
        return NoneSound()
    fullname = os.path.join('resources', name)
    try:
        sound = pygame.mixer.Sound(fullname)
    except pygame.error as message:
        print('Cannot load sound: {0}'.format(name))
        raise SystemExit(message)
    return sound


class spritesheet(object):
    def __init__(self, filename):
        try:
            self.sheet = pygame.image.load(filename).convert()
        except pygame.error as message:
            print('Unable to load spritesheet image: {0}'.format(filename))
            raise SystemExit(message)

    # Load a specific image from a specific rectangle
    def image_at(self, rectangle, colorkey = None):
        "Loads image from x,y,x+offset,y+offset"
        rect = pygame.Rect(rectangle)
        image = pygame.Surface(rect.size).convert()
        image.blit(self.sheet, (0, 0), rect)
        if colorkey is not None:
            if colorkey is -1:
                colorkey = image.get_at((0,0))
            image.set_colorkey(colorkey, pygame.RLEACCEL)
        return image

    # Load a whole bunch of images and return them as a list
    def images_at(self, rects, colorkey = None):
        "Loads multiple images, supply a list of coordinates"
        return [self.image_at(rect, colorkey) for rect in rects]

    # Load a whole strip of images
    def load_strip(self, rect, image_count, colorkey = None):
        "Loads a strip of images and returns them as a list"
        tups = [(rect[0]+rect[2]*x, rect[1]+rect[3]*y, rect[2], rect[3])
                for y in range(image_count[1]) for x in range(image_count[0])]
        return self.images_at(tups, colorkey)


class SpriteStripAnim(object):
    """sprite strip animator

    This class provides an iterator (iter() and next() methods), and a
    __add__() method for joining strips which comes in handy when a
    strip wraps to the next row.
    """

    def __init__(self, filename, rect, count, colorkey=None, loop=False, frames=1):
        """construct a SpriteStripAnim

        filename, rect, count, and colorkey are the same arguments used
        by spritesheet.load_strip.

        loop is a boolean that, when True, causes the next() method to
        loop. If False, the terminal case raises StopIteration.

        frames is the number of ticks to return the same image before
        the iterator advances to the next image.
        """
        self.filename = os.path.join('resources', filename)
        ss = spritesheet(self.filename)
        self.images = ss.load_strip(rect, count, colorkey)
        self.i = 0
        self.loop = loop
        self.frames = frames
        self.f = frames

    def iter(self):
        self.i = 0
        self.f = self.frames
        return self

    def next(self):
        if self.i >= len(self.images):
            if not self.loop:
                raise StopIteration
            else:
                self.i = 0
        image = self.images[self.i]
        self.f -= 1
        if self.f == 0:
            self.i += 1
            self.f = self.frames
        return image

    def __add__(self, ss):
        self.images.extend(ss.images)
        return self


# Sprite class with a draw function
class DrawSprite(pygame.sprite.Sprite):
    def draw(self, screen):
        screen.blit(self.image, self.rect)


# Group class that relies on the DrawSprite draw function
class DrawGroup(pygame.sprite.Group):
    def draw(self, screen):
        for sprite in self.sprites():
            sprite.draw(screen)
