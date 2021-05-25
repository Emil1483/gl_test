import numpy as np
import  vector
from math import floor

def pixels_from_agents(width, height, agents):
    pixels = [0.0] * width * height
    for agent in agents:
        pos = agent.pos
        index = floor(pos.y) * width + floor(pos.x)
        pixels[int(index)] = 5.0
    return np.array(pixels).astype('f4')

class Agent:
    def __init__(self, size, pos, vel):
        self.size = size
        self.pos = pos
        self.vel = vel
    
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