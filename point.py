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
                    color = vec3(angle, 0.50, 1.00);
                }
            ''',
        )

        self.transform = self.ctx.program(
            vertex_shader='''
            #version 330

            in vec3 in_vert;

            out vec3 out_vert;

            void main() {
                vec2 vel = vec2(cos(in_vert.z), sin(in_vert.z));
                out_vert = vec3(in_vert.xy + vel * 0.001, in_vert.z);
            }
        ''',
            varyings=['out_vert']
        )
        self.num_agents = 1_000

        agents = np.array([agent() for _ in range(self.num_agents)])
        self.agents_buffer1 = self.ctx.buffer(agents.astype('f4'))
        self.agents_buffer2 = self.ctx.buffer(reserve=self.agents_buffer1.size)
        self.vao = self.ctx.vertex_array(self.prog, self.agents_buffer1, 'in_vert')

        self.transform_vao = self.ctx.simple_vertex_array(self.transform, self.agents_buffer1, 'in_vert')

    def render(self, time, frame_time):
        self.ctx.enable_only(moderngl.PROGRAM_POINT_SIZE | moderngl.BLEND)
        self.ctx.blend_func = moderngl.ADDITIVE_BLENDING

        self.transform_vao.transform(self.agents_buffer2, vertices=self.num_agents * 3)

        self.vao.render(mode=moderngl.POINTS)

        self.ctx.copy_buffer(self.agents_buffer1, self.agents_buffer2)

if __name__ == '__main__':
    Particles.run()