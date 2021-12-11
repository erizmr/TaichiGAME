from __future__ import annotations
from typing import List, Optional

try:
    from taichi.ui.gui import GUI  # for taichi >= 0.8.7
except ImportError:
    print('taichi < 0.8.7 import gui \'from taichi.misc._gui\'')
    print('so feel free for this import error')
    from taichi.misc._gui import GUI

import numpy as np

from ..math.matrix import Matrix
from ..dynamics.phy_world import PhysicsWorld
from ..dynamics.body import Body
from ..collision.broad_phase.dbvh import DBVH
from ..dynamics.constraint.contact import ContactMaintainer


class Camera():
    class Viewport():
        def __init__(self,
                     top_left: Matrix = Matrix([0.0, 600.0], 'vec'),
                     bot_right: Matrix = Matrix([800.0, 0.0], 'vec')):

            assert top_left.x < bot_right.x
            assert top_left.y > bot_right.y

            self._top_left: Matrix = top_left
            self._bot_right: Matrix = bot_right

        @property
        def width(self) -> float:
            return self._bot_right.x - self._top_left.x

        @width.setter
        def width(self, width: float) -> None:
            self._bot_right.x = self._top_left.x + width

        @property
        def height(self) -> float:
            return self._top_left.y - self._bot_right.y

        @height.setter
        def height(self, height: float) -> None:
            self._top_left.y = self._bot_right.y + height

        def set_value(self, width: float, height: float):
            self.width = width
            self.height = height

    def __init__(self):
        self._visible: bool = True
        self._aabb_visible: bool = True
        self._joint_visible: bool = True
        self._body_visible: bool = True
        self._axis_visible: bool = True
        self._dbvh_visible: bool = False
        self._tree_visible: bool = False
        self._grid_scale_line_visible: bool = False
        self._rotation_line_visible: bool = False
        self._center_visible: bool = False
        self._contact_visible: bool = False

        self._meter_to_pixel: float = 50.0
        self._pixel_to_meter: float = 0.02

        self._target_meter_to_pixel: float = 80.0
        self._target_pixel_to_meter: float = 0.02

        self._transform: Matrix = Matrix([0.0, 0.0], 'vec')
        self._origin: Matrix = Matrix([0.0, 0.0], 'vec')
        self._viewport = Camera.Viewport()

        self._world: Optional[PhysicsWorld] = None
        self._target_body: Optional[Body] = None
        self._dbvh: Optional[DBVH] = None
        #  self._tree: Optional[Tree] = None
        self._maintainer: Optional[ContactMaintainer] = None

        self._zoom_factor: float = 1.0
        self._restit: float = 2.0
        self._delta_time: float = 15.0
        self._axis_point_count: float = 20.0

    # render factory method
    def render(self, gui: GUI) -> None:
        if self.visible:
            assert self.world is not None

            # calc the 'meter to pixel' scale according
            # to the 'target meter to pixel' set from
            # the wheel event
            inv_dt: float = 1.0 / self._delta_time
            scale: float = self._target_meter_to_pixel - self._meter_to_pixel
            if np.fabs(scale) < 0.1 or self._meter_to_pixel < 1.0:
                self._meter_to_pixel = self._target_meter_to_pixel
            else:
                self._meter_to_pixel -= (1.0 -
                                         np.exp(self._restit * inv_dt)) * scale

            if self.body_visible:
                self.render_body(gui)

            if self.joint_visible:
                self.render_joint(gui)

            if self.axis_visible:
                self.render_axis(gui)

            if self.aabb_visible:
                self.render_aabb(gui)

            if self.dbvh_visible:
                # self.render_dbvh(gui, self._)
                raise NotImplementedError

            if self.tree_visible:
                raise NotImplementedError

            if self.grid_scale_line_visible:
                self.render_grid_scale_line(gui)

            if self.contact_visible:
                self.render_contact(gui)

    @property
    def visible(self) -> bool:
        return self._visible

    @visible.setter
    def visible(self, visible: bool) -> None:
        self._visible = visible

    @property
    def aabb_visible(self) -> bool:
        return self._aabb_visible

    @aabb_visible.setter
    def aabb_visible(self, visible: bool) -> None:
        self._aabb_visible = visible

    @property
    def joint_visible(self) -> bool:
        return self._joint_visible

    @joint_visible.setter
    def joint_visible(self, visible: bool) -> None:
        self._joint_visible = visible

    @property
    def body_visible(self) -> bool:
        return self._body_visible

    @body_visible.setter
    def body_visible(self, visible: bool) -> None:
        self._body_visible = visible

    @property
    def axis_visible(self) -> bool:
        return self._axis_visible

    @axis_visible.setter
    def axis_visible(self, visible: bool) -> None:
        self._axis_visible = visible

    @property
    def dbvh_visible(self) -> bool:
        return self._dbvh_visible

    @dbvh_visible.setter
    def dbvh_visible(self, visible: bool) -> None:
        self._dbvh_visible = visible

    @property
    def tree_visible(self) -> bool:
        return self._tree_visible

    @tree_visible.setter
    def tree_visible(self, visible: bool) -> None:
        self._tree_visible = visible

    @property
    def grid_scale_line_visible(self) -> bool:
        return self._grid_scale_line_visible

    @grid_scale_line_visible.setter
    def grid_scale_line_visible(self, visible: bool) -> None:
        self._grid_scale_line_visible = visible

    @property
    def rot_line_visible(self) -> bool:
        return self._rotation_line_visible

    @rot_line_visible.setter
    def rot_line_visible(self, visible: bool) -> None:
        self._rotation_line_visible = visible

    @property
    def center_visible(self) -> bool:
        return self._center_visible

    @center_visible.setter
    def center_visible(self, visible: bool) -> None:
        self._center_visible = visible

    @property
    def contact_visible(self) -> bool:
        return self._contact_visible

    @contact_visible.setter
    def contact_visible(self, visible: bool) -> None:
        self._contact_visible = visible

    @property
    def meter_to_pixel(self) -> float:
        return self._meter_to_pixel

    @meter_to_pixel.setter
    def meter_to_pixel(self, val: float) -> None:
        # set the target 'meter_to_pixel' value
        # when in render,
        # clamp the scale value
        if val < 1.0:
            self._target_meter_to_pixel = 1.0
            self._target_pixel_to_meter = 1.0
            return

        self._target_meter_to_pixel = val
        self._target_pixel_to_meter = 1.0 / val

    @property
    def transform(self) -> Matrix:
        return self._transform

    @transform.setter
    def transform(self, trans: Matrix) -> None:
        self._transform = trans

    @property
    def world(self) -> PhysicsWorld:
        assert self._world is not None
        return self._world

    @world.setter
    def world(self, world: PhysicsWorld) -> None:
        self._world = world

    @property
    def target_body(self) -> Body:
        assert self._target_body is not None
        return self._target_body

    @target_body.setter
    def target_body(self, body: Body) -> None:
        self._target_body = body

    @property
    def zoom_factor(self) -> float:
        return self._zoom_factor

    @zoom_factor.setter
    def zoom_factor(self, factor: float) -> None:
        self._zoom_factor = factor

    @property
    def viewport(self) -> Viewport:
        return self._viewport

    @viewport.setter
    def viewport(self, viewport: Viewport) -> None:
        self._viewport = viewport

        tmp: List[float] = []
        tmp.append(
            (self._viewport._top_left.x + self._viewport._bot_right.x) * 0.5)
        tmp.append(
            (self._viewport._top_left.y + self._viewport._bot_right.y) * 0.5)
        self._origin.set_value(tmp)

    def world_to_screen(self, pos: Matrix) -> Matrix:
        orign: Matrix = Matrix([
            self._origin.x + self._transform.x,
            self._origin.y - self._transform.y
        ], 'vec')

        return Matrix([
            orign.x + pos.x * self._meter_to_pixel,
            orign.y - pos.y * self._meter_to_pixel
        ], 'vec')

    def screen_to_world(self, pos: Matrix) -> Matrix:
        orign: Matrix = Matrix([
            self._origin.x + self._transform.x,
            self._origin.y - self._transform.y
        ], 'vec')

        res: Matrix = pos - orign
        res.y = -res.y
        res *= self._pixel_to_meter

        return res

    @property
    def dbvh(self) -> DBVH:
        assert self._dbvh is not None
        return self._dbvh

    @dbvh.setter
    def dbvh(self, dbvh: DBVH) -> None:
        self._dbvh = dbvh

    # @property
    # def tree(self) -> Tree:
    #     return self._tree

    # @tree.setter
    # def tree(self, tree: Tree):
    #     self._tree = tree

    @property
    def delta_time(self) -> float:
        return self._delta_time

    @delta_time.setter
    def delta_time(self, time: float) -> None:
        self._delta_time = time

    @property
    def maintainer(self) -> ContactMaintainer:
        assert self._maintainer is not None
        return self._maintainer

    @maintainer.setter
    def maintainer(self, maintainer: ContactMaintainer) -> None:
        self._maintainer = maintainer

    def render_body(self, gui: GUI) -> None:
        raise NotImplementedError

    def render_joint(self, gui: GUI) -> None:
        raise NotImplementedError

    def render_axis(self, gui: GUI) -> None:
        raise NotImplementedError

    def render_aabb(self, gui: GUI) -> None:
        raise NotImplementedError

    def render_tree(self, gui: GUI, node_idx: int) -> None:
        raise NotImplementedError

    def render_contact(self, gui: GUI) -> None:
        raise NotImplementedError

    def render_grid_scale_line(self, gui: GUI) -> None:
        raise NotImplementedError

    def render_dbvh(self, gui: GUI, node: DBVH.Node) -> None:
        raise NotImplementedError
