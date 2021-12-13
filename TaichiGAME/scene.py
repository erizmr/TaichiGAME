from __future__ import annotations
from typing import Union

import taichi as ti

try:
    from taichi.ui.gui import GUI  # for taichi >= 0.8.7
except ImportError:
    print('taichi < 0.8.7 import gui \'from taichi.misc._gui\'')
    print('so feel free for this import error')
    from taichi.misc._gui import GUI

import numpy as np

from .common.camera import Camera
from .dynamics.phy_world import PhysicsWorld
from .collision.broad_phase.tree import Tree
from .math.matrix import Matrix


class Scene():
    def __init__(self, width: int = 1280, height: int = 720):
        self._gui: GUI = GUI('TaichiGAME',
                             res=(width, height),
                             background_color=ti.rgb_to_hex(
                                 [50 / 255.0, 50 / 255.0, 50 / 255.0]))
        # the physics world, all sim is run in physics world
        self._world: PhysicsWorld = PhysicsWorld()
        self._dbvt: Tree = Tree()
        # the view camera, all viewport scale is in camera
        self._cam: Camera = Camera()

        # physics init settings
        self._world.grav = Matrix([0.0, -9.8], 'vec')
        self._world._linear_vel_damping = 0.1
        self._world.air_fric_coeff = 0.8
        self._world.ang_vel_damping = 0.1
        self._world.damping_ena = True
        self._world.pos_iter = 8
        self._world.vel_iter = 6

        # camera init settings
        self._cam.viewport = Camera.Viewport(Matrix([0.0, height], 'vec'),
                                             Matrix([width, 0.0], 'vec'))
        self._cam.aabb_visible = False
        self._cam.dbvh_visible = False
        self._cam.tree_visible = False
        self._cam.axis_visible = True
        self._cam.body_visible = True
        self._cam.grid_scale_line_visible = False
        self._cam._world = self._world
        self._cam._dbvt = self._dbvt

        self._mouse_pos: Matrix = Matrix([0.0, 0.0], 'vec')
        # the right-mouse btn drag move flag(change viewport)
        self._mouse_viewport_move: bool = False

        self.radius = self._gui.slider('Radius', 1, 50, step=1)
        self.xcoor = self._gui.label('X-coordinate')
        self.okay = self._gui.button('OK')
        self.xcoor.value = 0.5
        self.radius.value = 10

    def physics_sim(self) -> None:
        pass

    def render(self) -> None:
        self._cam.render(self._gui)

    def handle_left_mouse_event(self, state: Union[GUI.PRESS, GUI.RELEASE],
                                x: float, y: float) -> None:

        self._mouse_pos = self._cam.screen_to_world(Matrix([x, y], 'vec'))
        if state == GUI.PRESS:
            pass
        else:
            pass

    def handle_right_mouse_event(self, state: Union[GUI.PRESS,
                                                    GUI.RELEASE]) -> None:
        if state == GUI.PRESS:
            self._mouse_viewport_move = True
        else:
            self._mouse_viewport_move = False

    def handle_mouse_move_event(self, x: float, y: float) -> None:
        cur_pos: Matrix = self._cam.screen_to_world(Matrix([x, y], 'vec'))
        delta_pos: Matrix = cur_pos - self._mouse_pos

        if self._mouse_viewport_move:
            # print(f'delta_pos1: {delta_pos}')
            delta_pos *= self._cam.meter_to_pixel
            # print(f'delta_pos2: {delta_pos}')
            # 0.5 just a hack value for equal radio move offset
            # 33.0 is init meter_to_pixel value
            self._cam.transform += delta_pos * 0.5 * (33.0 /
                                                      self._cam.meter_to_pixel)
        else:
            pass

        self._mouse_pos = cur_pos
        # print(f'({self._mouse_pos.x}, {self._mouse_pos.y}')

    def handle_wheel_event(self, y: float) -> None:
        # NOTE: need to set the sef._cam  the value scale
        # zoom in
        if y > 0:
            self._cam.meter_to_pixel += self._cam.meter_to_pixel / 4
        else:
            self._cam.meter_to_pixel -= self._cam.meter_to_pixel / 4

    def show(self) -> None:
        while self._gui.running:
            self.physics_sim()
            self.render()

            for e in self._gui.get_events():
                if e.key == ti.GUI.ESCAPE:
                    exit()

                elif e.key == ti.GUI.LMB:
                    self.handle_left_mouse_event(e.type, e.pos[0], e.pos[1])

                elif e.key == ti.GUI.RMB:
                    self.handle_right_mouse_event(e.type)

                elif e.key == ti.GUI.MOVE:
                    self.handle_mouse_move_event(e.pos[0], e.pos[1])

                elif e.key == ti.GUI.WHEEL:
                    self.handle_wheel_event(e.delta[1])

                elif e.key == ti.GUI.UP:
                    print("press up key")

                elif e.key == ti.GUI.DOWN:
                    print("press down key start")

                elif e.key == ti.GUI.LEFT:
                    print("press LEFT key restart")

                elif e.key == ti.GUI.RIGHT:
                    print("press right key")
                elif e.key == 'a':
                    self.xcoor.value -= 0.05
                elif e.key == 'd':
                    self.xcoor.value += 0.05
                elif e.key == 's':
                    self.radius.value -= 1
                elif e.key == 'w':
                    self.radius.value += 1
                elif e.key == self.okay:
                    print('OK clicked')

            self._gui.circle((self.xcoor.value, 0.5), radius=self.radius.value)
            self._gui.show()
