import numpy as np

import moderngl
import moderngl_window as mglw

def agent(width, height):
    a = np.random.uniform(0.0, np.pi * 2.0)
    return np.array([
        np.random.uniform(0, width),
        np.random.uniform(0, height),
        np.random.uniform(0.0, np.pi * 2.0),
    ]).astype('f4')

class Particles(mglw.WindowConfig):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.prog = self.ctx.program(
            vertex_shader='''
                #version 330

                in vec2 in_vert;
                in float in_angle;

                out float out_angle;

                void main() {
                    gl_Position = vec4(in_vert, 0.0, in_angle);
                    out_angle = in_angle;
                }
            ''',
            fragment_shader='''
                #version 330

                in float in_angle;

                out vec4 f_color;

                void main() {
                    f_color = vec4(in_angle / 4, 0.50, 1.00, 1.0);
                }
            ''',
        )

        self.transform = self.ctx.program(
            vertex_shader='''
            #version 330

            uniform vec2 Acc;

            in vec2 in_pos;
            in float in_angle;

            out vec2 out_pos;
            out float out_angle;

            void main() {
                vec2 vel = vec2(cos(in_angle), sin(in_angle));
                out_pos = in_pos + vel;
                out_angle = in_angle;
            }
        ''',
            varyings=['out_pos', 'out_angle']
        )

        self.num_agents = 100

        self.vbo1 = self.ctx.buffer(b''.join(agent(*self.window_size) for _ in range(self.num_agents)))
        self.vbo2 = self.ctx.buffer(reserve=self.vbo1.size)

        self.vao = self.ctx.simple_vertex_array(self.transform, self.vbo1, 'in_pos', 'in_angle')

        self.render_vao = self.ctx.vertex_array(self.prog, self.vbo1, 'in_vert', 'in_angle')

    def render(self, time, frame_time):
        self.ctx.clear(1.0, 1.0, 1.0)
        self.ctx.point_size = 5.0

        self.render_vao.render(moderngl.POINTS, self.num_agents)
        self.vao.transform(self.vbo2, moderngl.POINTS, self.num_agents)
        self.ctx.copy_buffer(self.vbo1, self.vbo2)

if __name__ == '__main__':
    Particles.run()