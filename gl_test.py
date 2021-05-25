import struct
import moderngl
from math import ceil

ctx = moderngl.create_context(standalone=True)

program = ctx.program(
    vertex_shader="""
    #version 330

    // Output values for the shader. They end up in the buffer.
    out float value;
    out float product;

    void main() {
        // Implicit type conversion from int to float will happen here
        value = gl_VertexID;

        float x = ceil(value / pow(21, 2)) - 11;
        float y = mod(ceil(value / 21), 21) - 10;
        float z = mod(value, 21)  - 10;

        product = pow(x, 3) + pow(y, 3) + pow(z, 3);
        if (product >= 0 && product <= 10) {
            product = 1;
        } else {
            product = 0;
        }
    }
    """,
    #! What out varyings to capture in our buffer!
    varyings=["value", "product"],
)

NUM_VERTICES = 21**3

#! We always need a vertex array in order to execute a shader program.
#! Our shader doesn't have any buffer inputs, so we give it an empty array.
vao = ctx.vertex_array(program, [])

#! Create a buffer allocating room for 20 32 bit floats
buffer = ctx.buffer(reserve=NUM_VERTICES * 2 * 4)

#! Start a transform with buffer as the destination.
#! We force the vertex shader to run 10 times
vao.transform(buffer, vertices=NUM_VERTICES)

#! Unpack the 20 float values from the buffer (copy from graphics memory to system memory).
#! Reading from the buffer will cause a sync (the python program stalls until the shader is done)
num = 2 * NUM_VERTICES
data = struct.unpack(str(num) + "f", buffer.read())
for i in range(0, num, 2):
    good = data[i+1] ==  1

    if not good: continue

    id = data[i]
    x = ceil(id / 21**2) - 11;
    y = ceil(id / 21) % 21 - 10;
    z = id % 21  - 10;

    print(f"{x}^3 + {y}^3 + {z}^3")