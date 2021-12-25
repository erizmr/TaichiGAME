from typing import List

import numpy as np
import taichi as ti

from .common.config import Config
from .common.ti_viewport import Viewport
from .dynamics.ti_phy_world import PhysicsWorld
from .frame import Frame

@ti.data_oriented
class Scene():
    def __init__(self, name: str, width: int = 1280, height: int = 720):
        self._gui = ti.GUI(name,
                           res=(width, height),
                           background_color=Config.BackgroundColor)

        # physics world
        self._world = PhysicsWorld()
        # calcuate step
        self._fps = 120
        self._dt = 1 / self._fps
        # viewport system
        self._viewport = Viewport(ti.Vector([0, height]), ti.Vector([width,
                                                                     0]))
        self._origin: ti.Vector = ti.Vector(
            [self._viewport.width / 2.0, self._viewport.height / 2.0])
        self._xform: ti.Vector = ti.Vector([0.0, 0.0])
        # zoom system
        self._meter_to_pixel: float = 33.0
        self._pixel_to_meter: float = 1 / self._meter_to_pixel
        self._target_meter_to_pixel: float = 53.0
        self._target_pixel_to_meter: float = 1 / self._target_meter_to_pixel
        self._restit: float = 2.0
        self._delta_time: float = 15.0
        # axis system
        self._axis_p_cnt: int = 10
        self._axis_p_list = ti.Vector.field(2,
                                            float,
                                            shape=4 * self._axis_p_cnt)
        self._axis_lin_st = ti.Vector.field(2, float, shape=2)
        self._axis_lin_ed = ti.Vector.field(2, float, shape=2)

        # mouse
        # NOTE: some algorithm need to cacluate the pos's len
        # in init state
        self._mouse_pos: ti.Vector = ti.Vector([1.0, 1.0])
        # the right-mouse btn drag move flag(change viewport)
        self._mouse_viewport_move: bool = False

        # extern frame table
        self._ext_frame_list: List[Frame] = []
        self._ext_frame_idx: int = 0

    def physics_sim(self) -> None:
        self._world.step_velocity(self._dt)
        self._world.step_position(self._dt)

    def render(self) -> None:
        self.smooth_scale()
        self.render_axis()
        self.render_body()

    def register_frame(self, frame: Frame) -> None:
        self._ext_frame_list.append(frame)

    def remove_frame(self, frame: Frame) -> None:
        # NOTE: need to check if exist first
        self._ext_frame_list.remove(frame)

    def clear_all(self) -> None:
        self._world.clear_all_bodies()
        self._world.clear_all_joints()
        # self._maintainer.clear_all()
        # self._dbvt.clear_all()

    def calc_nxt_frame(self, delta: int) -> None:
        ext_len: int = len(self._ext_frame_list)
        assert -ext_len <= delta <= ext_len

        self._ext_frame_idx = Config.clamp(self._ext_frame_idx, 0, ext_len - 1)
        # NOTE: the sign of mod in python depend on dividend
        self._ext_frame_idx = (self._ext_frame_idx + delta) % ext_len

    def init_frame(self) -> None:
        self.change_frame(0)
        # set the data to the world
        self._world.init_data()

    def change_frame(self, delta: int) -> None:
        self.clear_all()
        self.calc_nxt_frame(delta)
        self._ext_frame_list[self._ext_frame_idx].load()

    @ti.func
    def world_to_screen(self, world, scale, origx, origy, xformx, xformy, vw,
                        vh):
        origin = ti.Vector([origx + xformx, origy + xformy])

        resx = (origin.x + world.x * scale) / vw
        resy = (origin.y + world.y * scale) / vh
        return ti.Vector([resx, resy])

    def screen_to_world(self, pos: ti.Vector) -> ti.Vector:
        orign: ti.Vector = ti.Vector(
            [self._origin.x + self._xform.x, self._origin.y + self._xform.y])

        vw: float = self._viewport.width
        vh: float = self._viewport.height

        res: ti.Vector = ti.Vector([0.0, 0.0])
        res.x = pos.x * vw
        res.y = pos.y * vh
        res = res - orign
        res = res * self._pixel_to_meter

        return res

    @ti.kernel
    def gen_axis_data(self, scale: float, origx: float, origy: float,
                      xformx: float, xformy: float, vw: float, vh: float):
        tmp = ti.Vector([0.0, 0.0])
        for i in range(-self._axis_p_cnt, self._axis_p_cnt + 1):
            tmp = self.world_to_screen(ti.Vector([i * 1.0, 0.0]), scale, origx,
                                       origy, xformx, xformy, vw, vh)
            self._axis_p_list[(i + self._axis_p_cnt) * 2] = tmp

            tmp = self.world_to_screen(ti.Vector([0.0, i * 1.0]), scale, origx,
                                       origy, xformx, xformy, vw, vh)
            self._axis_p_list[(i + self._axis_p_cnt) * 2 + 1] = tmp

        self._axis_lin_st[0] = self._axis_p_list[0]
        self._axis_lin_st[1] = self._axis_p_list[1]
        self._axis_lin_ed[0] = self._axis_p_list[4 * self._axis_p_cnt - 2]
        self._axis_lin_ed[1] = self._axis_p_list[4 * self._axis_p_cnt - 1]

    def render_axis(self) -> None:
        self.gen_axis_data(self._meter_to_pixel, self._origin.x,
                           self._origin.y, self._xform.x, self._xform.y,
                           self._viewport.width, self._viewport.height)

        self._gui.circles(self._axis_p_list.to_numpy(),
                          radius=2,
                          color=Config.AxisPointColor)

        self._gui.lines(begin=self._axis_lin_st.to_numpy(),
                        end=self._axis_lin_ed.to_numpy(),
                        color=Config.AxisLineColor)

    @ti.kernel
    def gen_body_data(self):
        pass

    def render_body(self) -> None:
        # self._world.random_set()
        self.gen_body_data()
        self._gui.lines(begin=self._world._poly_st.to_numpy(),
                        end=self._world._poly_ed.to_numpy(),
                        color=0x0000FF)
        self._gui.triangles(a=self._world._polytri_a.to_numpy(),
                            b=self._world._polytri_b.to_numpy(),
                            c=self._world._polytri_c.to_numpy(),
                            color=0x0000FF)
        # self._gui.circles(self._world._pos.to_numpy(),
        #                   radius=self._world._cir_radius.to_numpy(),
        #                   color=Config.FillColor)
        # self._gui.lines(begin=self._world._edg_st.to_numpy(),
                        # end=self._world._edg_ed.to_numpy(),
                        # color=0xFF0000)
        # self._gui.triangles(a=self._world._tri_a.to_numpy(),
        # b=self._world._tri_b.to_numpy(),
        # c=self._world._tri_c.to_numpy(),
        # color=0xFF0000)

    def handle_mouse_move_evt(self, x: float, y: float) -> None:
        cur_pos: ti.Vector = self.screen_to_world(ti.Vector([x, y]))
        delta_pos: ti.Vector = cur_pos - self._mouse_pos

        if self._mouse_viewport_move:
            delta_pos = delta_pos * self._meter_to_pixel
            # 0.5 just a hack value for equal radio move offset
            # 33.0 is init meter_to_pixel value
            self._xform = self._xform + delta_pos * 0.5 * (
                33.0 / self._meter_to_pixel)
        self._mouse_pos = cur_pos

        return

    def handle_right_mouse_evt(self, state) -> None:
        if state == ti.GUI.PRESS:
            self._mouse_viewport_move = True
        else:
            self._mouse_viewport_move = False

    def handle_wheel_evt(self, delta: float) -> None:
        if delta > 0:
            self.meter_to_pixel += self.meter_to_pixel / 4
        else:
            self.meter_to_pixel -= self.meter_to_pixel / 4

    def show(self):
        while self._gui.running:

            for e in self._gui.get_events():
                if e.key == ti.GUI.ESCAPE:
                    exit()

                elif e.key == ti.GUI.SPACE and e.type == ti.GUI.RELEASE:
                    pass

                elif e.key == ti.GUI.LMB:
                    pass

                elif e.key == ti.GUI.RMB:
                    self.handle_right_mouse_evt(e.type)

                elif e.key == ti.GUI.MOVE:
                    self.handle_mouse_move_evt(e.pos[0], e.pos[1])

                elif e.key == ti.GUI.WHEEL:
                    self.handle_wheel_evt(e.delta[1])

                elif e.key == ti.GUI.UP:
                    print("press up key")

                elif e.key == ti.GUI.DOWN:
                    pass

                elif e.key == ti.GUI.LEFT and e.type == ti.GUI.RELEASE:
                    pass

                elif e.key == ti.GUI.RIGHT and e.type == ti.GUI.RELEASE:
                    pass

            self.physics_sim()
            self.render()
            self._gui.show()

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

    def smooth_scale(self) -> None:
        # calc the 'meter to pixel' scale according
        # to the 'target meter to pixel' set from
        # the wheel event smooth animation
        inv_dt: float = 1.0 / self._delta_time
        scale: float = self._target_meter_to_pixel - self._meter_to_pixel
        if np.fabs(scale) < 0.1 or self._meter_to_pixel < 1.0:
            self._meter_to_pixel = self._target_meter_to_pixel
        else:
            self._meter_to_pixel -= (1.0 -
                                     ti.exp(self._restit * inv_dt)) * scale

        self._pixel_to_meter = 1.0 / self._meter_to_pixel
