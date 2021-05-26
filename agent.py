import numpy as np
from vector import Vector
from math import floor

def pixels_from_agents(width, height, agents):
    pixels = [0.0] * width * height
    for agent in agents:
        pos = agent.pos
        index = floor(pos.y) * width + floor(pos.x)
        pixels[int(index)] = 1.00001
    return np.array(pixels).astype('f4')

def agents_to_array(agents):
    result = []
    for agent in agents:
        result.append(agent.pos.x)
        result.append(agent.pos.y)
        result.append(agent.angle)
    return result

def update_agents(agents, data):
    for i in range(0, len(data), 3):
        pos_x = data[i]
        pos_y = data[i + 1]
        angle = data[i + 2]
        
        agents[i // 3].pos = Vector(pos_x, pos_y)
        agents[i // 3].angle = angle

class Agent:
    def __init__(self, size, pos, angle):
        self.size = size
        self.pos = pos
        self.angle = angle
    
    def update(self):
        self.pos += self.vel
        self.pos = self.pos.mod(self.size.x, self.size.y)
        # if self.pos.x > self.size.x:
        #     self.vel.array[0] *= -1
        # if self.pos.x < 0:
        #     self.vel.array[0] *= -1
        # if self.pos.y > self.size.y:
        #     self.vel.array[1] *= -1
        # if self.pos.y < 0:
        #     self.vel.array[1] *= -1
        # self.pos += self.vel