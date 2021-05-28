import numpy as np

import struct
import moderngl
import moderngl_window as mglw

def agent():
    a = np.random.uniform(0.0, np.pi * 2.0)
    return np.array([
        np.random.uniform(-1, 1),
        np.random.uniform(-1, 1),
        np.random.uniform(0.0, np.pi * 2.0),
    ]).astype('f4')

class Particles(mglw.WindowConfig):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.prog = self.ctx.program(
            vertex_shader='''
                #version 330

                in vec3 in_vert;

                out float angle;

                void main() {
                    gl_Position = vec4(in_vert.x, in_vert.y, 0.0, 1.0);
                    angle = in_vert.z;
                }
            ''',
            fragment_shader='''
                #version 330

                in float angle;

                out vec3 color;

                void main() {
                    color = vec3(angle, angle, angle);
                }
            ''',
        )

        self.transform = self.ctx.program(
            vertex_shader='''
            #version 330

            uniform float pi = 3.14159265;

            in vec2 in_pos;
            in float in_angle;

            out vec2 out_pos;
            out float out_angle;

            float random() {
                uint state = uint(in_pos.y * 2000 + in_pos.x);
                state ^= 2747636419u;
                state *= 2654435769u;
                state ^= state >> 16;
                state *= 2654435769u;
                state ^= state >> 16;
                state *= 2654435769u;
                return float(state) / 4294967295.0;
            }

            void main() {
                vec2 vel = vec2(cos(in_angle), sin(in_angle));
                out_pos = in_pos + vel * 0.002;
                out_angle = in_angle;

                if (out_pos.x <= -1 || out_pos.x >= 1 || out_pos.y <= -1 || out_pos.y >= 1) {
                    float x = min(0.99, max(-0.99, out_pos.x));
                    float y = min(0.99, max(-0.99, out_pos.y));
                    out_pos = vec2(x, y);
                    out_angle += pi / 2 + random() * pi;
                }
            }
        ''',
            varyings=['out_pos', 'out_angle']
        )
        self.num_agents = 100

        agents = np.array([agent() for _ in range(self.num_agents)])
        self.agents_buffer1 = self.ctx.buffer(agents.astype('f4'))
        self.agents_buffer2 = self.ctx.buffer(reserve=self.agents_buffer1.size)
        self.vao = self.ctx.vertex_array(self.prog, self.agents_buffer1, 'in_vert')

        self.transform_vao = self.ctx.simple_vertex_array(self.transform, self.agents_buffer1, 'in_pos', 'in_angle')

    def render(self, time, frame_time):
        self.ctx.point_size = 1.0

        self.transform_vao.transform(self.agents_buffer2, vertices=self.num_agents * 3)

        self.vao.render(mode=moderngl.POINTS)

        self.ctx.copy_buffer(self.agents_buffer1, self.agents_buffer2)

if __name__ == '__main__':
    Particles.run()