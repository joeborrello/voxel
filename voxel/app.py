#!/usr/bin/python2

import logging
import math
import sys
import random

import numpy
import OpenGL
OpenGL.ERROR_ON_COPY = True

from OpenGL.arrays import vbo
from OpenGL.GL import *
from OpenGL.GLUT import *

# PyOpenGL 3.0.1 introduces this convenience module...
import OpenGL.GL.shaders as glsl

import core


def bindable(func):
    """
    Attaches the 'bindable' attribute to the provided function.

    """
    func.bindable = True
    return func


class App(object):
    """
    This class provides an interface that can be called by GLUT and exposes
    the high level functions that allow a user to interact with the scene.
    """

    def __init__(self, config):
        self._keys = self._create_key_bindings(config)

        self._resolution = config.app.resolution
        self._sensitivity = config.app.sensitivity

        self._last_mouse_press = None
        self._last_orientation = None
        self._key_pressed = None

        # Build the shader program so that the renderer can be created.
        window = config.app.window
        shaders = config.shaders
        program = self._create_shader_program(shaders.vertex, shaders.fragment)
        self._renderer = core.Renderer(program, (window.width, window.height))

    @property
    def renderer(self):
        """
        The renderer used by the app.

        """
        return self._renderer

    @property
    def resolution(self):
        """
        The length of an edge of a voxel.

        """
        return self._resolution

    @property
    def sensitivity(self):
        """
        The mouse sensitivity.

        """
        return self._sensitivity

    def _create_key_bindings(self, config):
        """
        Bind keys to bindable functions.

        """
        bindings = {}
        for key, func in config.app.bindings.items():
            if key not in keymap:
                raise ValueError('Unrecognized key -- %s' % (key,))

            if not hasattr(self, func):
                raise ValueError('Unrecognized binding -- %s' % (func,))

            method = getattr(self, func)
            if not hasattr(method, 'bindable'):
                raise ValueError('%s is not a bindable function' % (func,))

            bindings[keymap[key]] = getattr(self, func)

        return bindings

    def _create_shader_program(self, vertex_shaders, fragment_shaders):
        """
        Creates a shader program from the provided shaders, which are lists of
        paths to the vertex and fragment shaders respectively.

        """
        program = core.ShaderProgram()

        for shader in vertex_shaders:
            program.load_vertex_shader(shader)

        for shader in fragment_shaders:
            program.load_fragment_shader(shader)

        program.build()

        return program

 
    def add_point(self, x, y, z, c):
        """
        Add a point to renderer. The point will be re-mapped to a 3D lattice
        defined by the resolution of the app.
        """
        x = self.resolution * int(x / self.resolution)
        y = self.resolution * int(y / self.resolution)
        z = self.resolution * int(z / self.resolution)
        h = 0.5 * self.resolution
        self.renderer.add_voxel(core.Voxel(x, y, z, h, h, h, c.r, c.g, c.b, c.a))

    def resize(self, width, height):
        """
        Called when the window is resized. The height and width of the new
        window size are passed in.

        """
        self.renderer.resize(width, height)

    def idle(self):
        """
        Called when the GLUT program is idle. This is where key presses are
        handled and we also call display to refresh the scene.

        """
        key = self._key_pressed
        if key is not None and key in self._keys:
            self._keys[key]()
        self.display()

    def display(self):
        """
        Called to refresh the scene.

        """
        self.renderer.display()

    @bindable
    def exit(self):
        """
        Forces the program to exit.

        """
        sys.exit(0)

    @bindable
    def move_forward(self):
        """
        Moves the camera forward.

        """
        self.renderer.camera.move_forward(20.0)

    @bindable
    def move_backward(self):
        """
        Moves the camera backward.

        """
        self.renderer.camera.move_backward(20.0)

    @bindable
    def move_down(self):
        """
        Moves the camera down.

        """
        self.renderer.camera.move_down(20.0)

    @bindable
    def move_up(self):
        """
        Moves the camera up.

        """
        self.renderer.camera.move_up(20.0)

    @bindable
    def move_left(self):
        """
        Moves the camera left.

        """
        self.renderer.camera.move_left(20.0)

    @bindable
    def move_right(self):
        """
        Moves the camera right.

        """
        self.renderer.camera.move_right(20.0)

    @bindable
    def roll_left(self):
        """
        Rotates the camera to the left along the forward/backward axis.

        """
        self.renderer.camera.roll(math.pi / 120.0)

    @bindable
    def roll_right(self):
        """
        Rotates the camera to the right along the forward/backward axis.

        """
        self.renderer.camera.roll(-math.pi / 120.0)

    @bindable
    def pitch_forward(self):
        """
        Rotates the camera forward along the left/right axis

        """
        self.renderer.camera.pitch(-math.pi / 120.0)

    @bindable
    def pitch_backward(self):
        """
        Rotates the camera backward along the left/right axis

        """
        self.renderer.camera.pitch(math.pi / 120.0)

    @bindable
    def yaw_left(self):
        """
        Rotates the camera left along the vertical axis

        """
        self.renderer.camera.yaw(math.pi / 120.0)

    @bindable
    def yaw_right(self):
        """
        Rotates the camera right along the vertical axis

        """
        self.renderer.camera.yaw(-math.pi / 120.0)

    def keyboard(self, *args):
        """
        Called when a key is pressed.

        """
        self._key_pressed = args[0]

    def keyboard_up(self, *args):
        """
        Called when a key is released.

        """
        self._key_pressed = None

    def mouse_move(self, *args):
        """
        Called when the mouse moves. The args parameters contains the 2D
        position of the mouse in window co-ordinates.

        """
        xn, yn = args
        if self._last_mouse_press:
            x0, y0 = self._last_mouse_press
            delta_x = xn - x0
            delta_y = yn - y0
            scale = self.sensitivity * math.pi / 360.0

            # reset the camera to its original orientation
            self.renderer.camera.orientation = self._last_orientation

            # now move the camera to the new orientation relative to its
            # original orientation
            self.renderer.camera.yaw(-scale * delta_x)
            self.renderer.camera.pitch(-scale * delta_y)

    def mouse_press(self, *args):
        """
        Called when a mouse button is pressed or released. The args parameter
        is a tuple with 4 elements,

            (button, pressed, x, y)

        The first element indicates which button is pressed, the second is a 0
        (released) or 1 (pressed), and final two are the position of the mouse
        in window co-ordinates.

        """
        button, up, x, y = args
        if button == 0:
            if up:
                self._last_mouse_press = None
                self._last_orientation = None
            else:
                self._last_mouse_press = (x, y)
                self._last_orientation = self.renderer.camera.orientation


class Config(object):
    """
    A utility class for represented a dictionary of nested data as an object.
    """

    def __init__(self, datadict):
        """
        Creates a Config object using the providing dictionary.

        """
        for k, v in datadict.items():
            try:
                setattr(self, k, Config(v))
            except:
                setattr(self, k, v)

    def __repr__(self):
        """
        Returns the representation of the Config object.

        """
        return repr(self.__dict__)

    def items(self):
        """
        Returns a list of the key-value pairs.

        """
        return self.__dict__.items()


keymap = {
        'key_escape': '\x1b',
        'key_a': 'a',
        'key_b': 'b',
        'key_c': 'c',
        'key_d': 'd',
        'key_e': 'e',
        'key_f': 'f',
        'key_g': 'g',
        'key_h': 'h',
        'key_i': 'i',
        'key_j': 'j',
        'key_k': 'k',
        'key_l': 'l',
        'key_m': 'm',
        'key_n': 'n',
        'key_o': 'o',
        'key_p': 'p',
        'key_q': 'q',
        'key_r': 'r',
        'key_s': 's',
        'key_t': 't',
        'key_u': 'u',
        'key_v': 'v',
        'key_w': 'w',
        'key_x': 'x',
        'key_y': 'y',
        'key_z': 'z',
        'key_A': 'A',
        'key_B': 'B',
        'key_C': 'C',
        'key_D': 'D',
        'key_E': 'E',
        'key_F': 'F',
        'key_G': 'G',
        'key_H': 'H',
        'key_I': 'I',
        'key_J': 'J',
        'key_K': 'K',
        'key_L': 'L',
        'key_M': 'M',
        'key_N': 'N',
        'key_O': 'O',
        'key_P': 'P',
        'key_Q': 'Q',
        'key_R': 'R',
        'key_S': 'S',
        'key_T': 'T',
        'key_U': 'U',
        'key_V': 'V',
        'key_W': 'W',
        'key_X': 'X',
        'key_Y': 'Y',
        'key_Z': 'Z',
   }
