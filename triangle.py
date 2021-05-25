import moderngl_window as mglw
import numpy as np

class Triange(mglw.WindowConfig):
    title = "Cum"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.prog = self.ctx.program(
            vertex_shader='''
                #version 330

                in vec4 in_vert;

                void main() {
                    gl_Position = in_vert;
                }
            ''',
            fragment_shader='''
                #version 330

                out vec4 f_color;

                void main() {
                    f_color = vec4(1, 0.5, 1.0, 0.1);
                }
            ''',
        )

        vertices = np.array([
            0.0, 0.8, 0, 10.0,
            -0.6, -0.8, 0, 0.1,
            0.6, -0.8, 0, 1.0
        ], dtype='f4')

        self.vbo = self.ctx.buffer(vertices)
        self.vao = self.ctx.simple_vertex_array(self.prog, self.vbo, 'in_vert')

    def render(self, time, frame_time):
        self.ctx.clear(1.0, 1.0, 1.0)
        self.vao.render()

Triange.run()