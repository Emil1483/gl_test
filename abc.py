import struct
import moderngl
import numpy as np

ctx = moderngl.create_context(standalone=True)

program = ctx.program(
    vertex_shader="""
    #version 330

    in vec3 in_vert;

    out vec3 input;

    out float result;

    void main() {
        input = in_vert;
        result = pow(input.x, 3) + pow(input.y, 3) + pow(input.z, 3);
        if (result < 0 || result > 10) result = -1;
    }
    """,
    varyings=["input", "result"],
)

verts = []
size = 10
for a in range(-size, size + 1):
    for b in range(-size, size + 1):
        for c in range(-size, size + 1):
            verts.append(a)
            verts.append(b)
            verts.append(c)

vbo = ctx.buffer(np.array(verts, dtype='f4'))

vao = ctx.vertex_array(program, vbo, 'in_vert')

buffer = ctx.buffer(reserve=vbo.size * 4 // 3)

vao.transform(buffer)

data = struct.unpack(str(vbo.size * 4 // 12) + 'f', buffer.read())

for i in range(0, len(data), 4):
    expression, value = data[i : i + 3], data[i + 3]
    if value == -1: continue
    print(expression, value)