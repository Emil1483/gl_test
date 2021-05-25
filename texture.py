import numpy as np
import moderngl
import moderngl_window as mglw
import struct
from agent import *
from vector import *

# http://glslsandbox.com/e#375.15

class Texture(mglw.WindowConfig):
    title = "Texture"
    window_size = 800, 800

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.update_delay = 1 / 60  # updates per second
        self.last_updated = 0

        self.width, self.height = 300, 300;
        self.wnd.fixed_aspect_ratio = self.width / self.height

        pixels = np.round(np.random.rand(self.width, self.height)).astype('f4')

        self.num_agents = 100
        self.agents = [Agent(
            Vector(self.width, self.height),
            random_vector_in_range(self.width, self.height),
            random_unit_vector()) for _ in range(self.num_agents)]

        self.display_prog = self.ctx.program(
            vertex_shader='''
                #version 330

                in vec2 in_vert;
                in vec2 in_texcoord;

                out vec2 v_text;

                void main() {
                    v_text = in_texcoord;
                    gl_Position = vec4(in_vert, 0.0, 1.0);
                }
            ''',
            fragment_shader='''
                #version 330

                // Will read from texture bound to channel / locaton 0 by default
                uniform sampler2D Texture;

                // Interpolated texture coordinate from vertex shader
                in vec2 v_text;
                // The fragment ending up on the screen
                out vec4 f_color;

                void main() {
                    f_color = texture(Texture, v_text);
                }
            ''',
        )

        self.blend_prog = self.ctx.program(
            vertex_shader='''
                #version 330

                uniform sampler2D texture1;
                uniform sampler2D texture2;

                out float out_vert;

                void main() {
                    int width = textureSize(texture1, 0).x;
                    ivec2 in_text = ivec2(gl_VertexID % width, gl_VertexID / width);

                    float col1 = texelFetch(texture1, in_text, 0).r;
                    float col2 = texelFetch(texture2, in_text, 0).r;

                    if (col2 > 1) {
                        out_vert = col2;
                    } else {
                        out_vert = col1;
                    }
                }
            ''',
            varyings=['out_vert']
        )

        self.mold_prog = self.ctx.program(
            vertex_shader='''
                #version 330

                uniform sampler2D Texture;
                uniform vec2 in_vert;

                out float out_vert;

                void main() {
                    int width = textureSize(Texture, 0).x;
                    ivec2 in_text = ivec2(gl_VertexID % width, gl_VertexID / width);
                    if (in_text == in_vert) {
                        out_vert = 5.0;
                    } else {
                        vec4 val = texelFetch(Texture, in_text, 0);
                        out_vert = val.r;
                    }
                }
            ''',
            varyings=['out_vert']
        )

        self.transform_prog = self.ctx.program(
            vertex_shader='''
                #version 330

                uniform sampler2D Texture;
                uniform float weight[5] = float[] (0.227027, 0.1945946, 0.1216216, 0.054054, 0.016216);

                uniform int Horizontal;

                out float out_vert;

                float cell(int x, int y) {
                    ivec2 tSize = textureSize(Texture, 0).xy;
                    return texelFetch(Texture, ivec2((x + tSize.x) % tSize.x, (y + tSize.y) % tSize.y), 0).r;
                }

                void main() {
                    int width = textureSize(Texture, 0).x;
                    ivec2 in_text = ivec2(gl_VertexID % width, gl_VertexID / width);

                    float result = cell(in_text.x, in_text.y) * weight[0];

                    if (Horizontal == 1) {
                        for (int i = 1; i < 5; i++) {
                            result += cell(in_text.x + i, in_text.y) * weight[i];
                            result += cell(in_text.x - i, in_text.y) * weight[i];
                        }
                    } else {
                        for (int i = 1; i < 5; i++) {
                            result += cell(in_text.x, in_text.y + i) * weight[i];
                            result += cell(in_text.x, in_text.y - i) * weight[i];
                        }
                    }

                    out_vert = result * 0.99;
                }
            ''',
            varyings=['out_vert']
        )
        self.texture = self.ctx.texture((self.width, self.height), 1, pixels.tobytes(), dtype='f4')
        self.texture.filter = moderngl.NEAREST, moderngl.NEAREST
        self.texture.swizzle = 'RRR1'

        self.vbo = self.ctx.buffer(np.array([
            # x    y     u  v
            -1.0, -1.0,  0, 0,  # lower left
            -1.0,  1.0,  0, 1,  # upper left
            1.0,  -1.0,  1, 0,  # lower right
            1.0,   1.0,  1, 1,  # upper right
        ], dtype="f4"))
        self.vao = self.ctx.simple_vertex_array(self.display_prog, self.vbo, 'in_vert', 'in_texcoord')

        self.pbo = self.ctx.buffer(reserve=pixels.nbytes)

        self.mold_tao = self.ctx.vertex_array(self.mold_prog, [])
        self.mold_pbo = self.ctx.buffer(reserve=pixels.nbytes)

        self.blend_tao = self.ctx.vertex_array(self.blend_prog, [])
        self.blend_pbo = self.ctx.buffer(reserve=pixels.nbytes)

    def render(self, time, frame_time):
        self.ctx.clear(1.0, 1.0, 1.0)

        # Bind texture to channel 0
        self.texture.use(location=0)

        if time - self.last_updated > self.update_delay:
            # pbo = self.ctx.buffer(reserve=self.width * self.height * 4)
            # self.texture.read_into(pbo)

            # data = struct.unpack(str(self.width * self.height) + 'f', pbo.read())

            # pixels = np.array(data).astype('f4')

            # pixels[(self.height + 1) * self.width // 2] = 5

            # pixels = np.round(np.random.rand(self.width, self.height)).astype('f4')

            # self.texture = self.ctx.texture((self.width, self.height), 1, pixels.tobytes(), dtype='f4')
            # self.texture.filter = moderngl.NEAREST, moderngl.NEAREST
            # self.texture.swizzle = 'RRR1'
            # self.texture.use(location=0)
            # self.texture.write(self.pbo)
            # pixels = self.ctx.buffer(reserve=self.width * self.height)
            # self.texture.read_into(pixels)
            # pixels.write(b'f')
            # pixels.write(self.pbo)

            # self.mold_prog['in_vert'].value = self.width // 2, self.height // 2
            # self.mold_tao.transform(self.mold_pbo, vertices=self.width * self.height)
            # mold_texture = self.ctx.texture((self.width, self.height), 1, self.mold_pbo.read(), dtype='f4')
            # mold_texture.use(location=1)

            # pixels = [0] * self.width * self.height
            # pixels[(1 + self.height) * self.width // 2] = 15
            # pixels = np.array(pixels).astype('f4')

            for agent in self.agents: agent.update()

            pixels = pixels_from_agents(self.width, self.height, self.agents)
            mold_texture = self.ctx.texture((self.width, self.height), 1, pixels.tobytes(), dtype='f4')
            mold_texture.use(location=1)

            self.blend_prog['texture2'] = 1

            self.blend_tao.transform(self.blend_pbo, vertices=self.width * self.height)

            self.texture.write(self.blend_pbo)

            for i in range(2):
                self.transform_prog['Horizontal'].value = i % 2
                tao = self.ctx.vertex_array(self.transform_prog, [])
                tao.transform(self.pbo, vertices=self.width * self.height)
                self.texture.write(self.pbo)

            self.last_updated = time

        # Render the texture
        self.vao.render(moderngl.TRIANGLE_STRIP)

if __name__ == '__main__':
    Texture.run()