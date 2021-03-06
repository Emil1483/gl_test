import numpy as np
import moderngl
import moderngl_window as mglw
import struct
from agent import *
from vector import *

# http://glslsandbox.com/e#375.15

class Texture(mglw.WindowConfig):
    title = "Texture"
    window_size = 120, 120

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.update_delay = 1 / 60  # updates per second
        self.last_updated = 0

        self.width, self.height = self.window_size;
        self.wnd.fixed_aspect_ratio = self.width / self.height

        pixels = np.round(np.zeros((self.width, self.height))).astype('f4')

        self.num_agents = 100
        self.mold_renderer = self.ctx.program(
            vertex_shader='''
                #version 330

                uniform float width;
                uniform float height;

                in vec3 in_vert;

                void main() {
                    gl_Position = vec4(in_vert.x * 2 / width - 1, in_vert.y * 2 / height - 1, 0.0, 1.0);
                }
            ''',
            fragment_shader='''
                #version 330

                out vec3 color;

                void main() {
                    color = vec3(1.0, 1.0, 1.0);
                }
            ''',
        )

        self.mold_renderer['width'] = self.width
        self.mold_renderer['height'] = self.height

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

                uniform float speed;
                uniform float turn_speed;
                uniform float sensor_angle_spacing;
                uniform float sensor_offset_dist;

                uniform float pi = 3.14159265;

                in vec2 in_pos;
                in float in_angle;

                out vec2 out_pos;
                out float out_angle;

                float cell(int x, int y) {
                    ivec2 tSize = textureSize(Texture, 0).xy;
                    return texelFetch(Texture, ivec2((x + tSize.x) % tSize.x, (y + tSize.y) % tSize.y), 0).r;
                }

                float random() {
                    int width = textureSize(Texture, 0).x;
                    uint state = uint(in_pos.y * width + in_pos.x);
                    state ^= 2747636419u;
                    state *= 2654435769u;
                    state ^= state >> 16;
                    state *= 2654435769u;
                    state ^= state >> 16;
                    state *= 2654435769u;
                    return float(state) / 4294967295.0;
                }
                
                float sense(float angleOffset) {
                    float angle = in_angle + angleOffset;
                    vec2 senseDir = vec2(cos(angle), sin(angle));
                    vec2 sensePos = in_pos + senseDir * sensor_offset_dist;

                    float sum = 0.0;
                    for (int i = -1; i <= 1; i++) {
                        for (int j = -1; i <= 1; i++) {
                            vec2 pos = sensePos + vec2(i, j);
                            sum += cell(int(pos.x), int(pos.y));
                        }
                    }

                    return sum;
                }

                void main() {
                    vec2 vel = speed * vec2(cos(in_angle), sin(in_angle));
                    out_pos = in_pos + vel;

                    ivec2 tSize = textureSize(Texture, 0).xy;

                    float forward = sense(0);
                    float left = sense(-sensor_angle_spacing);
                    float right = sense(sensor_angle_spacing);

                    if (forward > left && forward > right) {
                        out_angle = in_angle;
                    } else if (forward < left && forward < right) {
                        out_angle = in_angle + (random() - 0.5) * 2 * turn_speed;
                    } else if (right > left) {
                        out_angle = in_angle + turn_speed;
                    } else if (right < left) {
                        out_angle = in_angle - turn_speed;
                    } else {
                        out_angle = in_angle;
                    }

                    if (out_pos.x < 0 || out_pos.x >= tSize.x || out_pos.y < 0 || out_pos.y >= tSize.y) {
                        float x = min(tSize.x - 0.01, max(0, out_pos.x));
                        float y = min(tSize.y - 0.01, max(0, out_pos.y));
                        out_pos = vec2(x, y);
                        out_angle = random() * 2 * pi;
                    }
                }
            ''',
            varyings=['out_pos', 'out_angle']
        )

        self.transform_prog = self.ctx.program(
            vertex_shader='''
                #version 330

                uniform sampler2D Texture;

                out float out_vert;

                float cell(int x, int y) {
                    ivec2 tSize = textureSize(Texture, 0).xy;
                    return texelFetch(Texture, ivec2((x + tSize.x) % tSize.x, (y + tSize.y) % tSize.y), 0).r;
                }

                void main() {
                    int width = textureSize(Texture, 0).x;
                    ivec2 in_text = ivec2(gl_VertexID % width, gl_VertexID / width);

                    float blurResult = 0.0;

                    for (int i = -1; i <= 1; i++) {
                        for (int j = -1; j <= 1; j++) {
                            blurResult += cell(in_text.x + i, in_text.y + j);
                        }
                    }
                    blurResult /= 9;

                    float diffused = mix(cell(in_text.x, in_text.y), blurResult, 0.2);

                    out_vert = max(0, diffused - 0.07);
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

        self.blend_tao = self.ctx.vertex_array(self.blend_prog, [])
        self.blend_pbo = self.ctx.buffer(reserve=pixels.nbytes)

        self.mold_prog['speed'] = 1.0
        self.mold_prog['turn_speed'] = 0.25
        self.mold_prog['sensor_angle_spacing'] = 0.4
        self.mold_prog['sensor_offset_dist'] = 3.0

        agents = []
        radius = min(self.height, self.width) // 3
        for _ in range(self.num_agents):
            a = random.uniform(0, 2 * math.pi)
            r = random.uniform(0, radius)
            pos = Vector(
                self.width // 2 + r * math.cos(a),
                self.height // 2 + r * math.sin(a),
            )
            agents.append(pos.x)
            agents.append(pos.y)
            agents.append(a + math.pi)

        self.mold_vbo1 = self.ctx.buffer(np.array(agents).astype('f4'))
        self.mold_vbo2 = self.ctx.buffer(reserve=self.mold_vbo1.size)
        self.mold_transform_vao  = self.ctx.simple_vertex_array(self.mold_prog, self.mold_vbo1, 'in_pos', 'in_angle')
        self.mold_renderer_vao = self.ctx.vertex_array(self.mold_renderer, self.mold_vbo1, 'in_vert')

        self.mold_texture = self.ctx.texture((self.width, self.height), 1, dtype='f4')

        self.blend_prog['texture2'] = 1

    def render(self, time, frame_time):
        self.ctx.enable_only(moderngl.PROGRAM_POINT_SIZE | moderngl.BLEND)
        self.ctx.blend_func = moderngl.ADDITIVE_BLENDING

        # Bind texture to channel 0
        self.texture.use(location=0)
        self.mold_texture.use(location=1)

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

            # for agent in self.agents: agent.update()

            # self.vbo = self.ctx.buffer(np.array([
            #     # x    y     u  v
            #     -1.0, -1.0,  0, 0,  # lower left
            #     -1.0,  1.0,  0, 1,  # upper left
            #     1.0,  -1.0,  1, 0,  # lower right
            #     1.0,   1.0,  1, 1,  # upper right
            #     ], dtype="f4"))
            # self.vao = self.ctx.simple_vertex_array(self.display_prog, self.vbo, 'in_vert', 'in_texcoord')

            # uniform float speed;
            # uniform float turn_speed;
            # uniform float sensor_angle_spacing;
            # uniform float sensor_offset_dist;

            # mold_vbo = self.ctx.buffer(np.array(agents_to_array(self.agents), dtype='f4'))
            # mold_tao = self.ctx.vertex_array(self.mold_prog, mold_vbo, 'in_pos', 'in_angle')
            # mold_pbo = self.ctx.buffer(reserve=self.num_agents * 3 * 4)
            # mold_tao.transform(mold_pbo)
            # data = struct.unpack(str(mold_pbo.size // 4) + 'f', mold_pbo.read())
            # update_agents(self.agents, data)

            # pixels = pixels_from_agents(self.width, self.height, self.agents)
            # mold_texture = self.ctx.texture((self.width, self.height), 1, pixels.tobytes(), dtype='f4')
            # mold_texture.use(location=1)
        self.mold_transform_vao.transform(self.mold_vbo2)

        buffer = self.ctx.buffer(reserve=self.width * self.height)
        self.mold_renderer_vao.render_indirect(buffer, mode=moderngl.POINTS)
        self.mold_texture.write(buffer)

        self.ctx.copy_buffer(self.mold_vbo1, self.mold_vbo2)

        self.blend_tao.transform(self.blend_pbo, vertices=self.width * self.height)

        self.texture.write(self.blend_pbo)

        tao = self.ctx.vertex_array(self.transform_prog, [])
        tao.transform(self.pbo, vertices=self.width * self.height)
        self.texture.write(self.pbo)

        self.last_updated = time

        # Render the texture
        self.vao.render(moderngl.TRIANGLE_STRIP)

if __name__ == '__main__':
    Texture.run()