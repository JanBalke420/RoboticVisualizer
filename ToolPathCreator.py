import numpy as np
import matplotlib.pyplot as plt

def normalize_vector(vec):
    vec_len = np.sqrt(np.square(vec[0])+np.square(vec[1])+np.square(vec[2]))
    new_vec = np.multiply(vec, 1/vec_len)
    return new_vec



# circle with radius 1
def circle(segments, offset):
    tool_path = []
    for i in range(segments):
        segment_radians = (i/segments)*np.pi*2

        x = np.cos(segment_radians)+offset[0]
        y = np.sin(segment_radians)+offset[1]
        z = np.sin(segment_radians*2)+offset[2]

        nx = np.cos(segment_radians)
        ny = np.sin(segment_radians)
        nz = np.abs(np.cos(segment_radians))
        normal = normalize_vector([nx,ny,nz])

        tool_step = [x*1000,y*1000,z*1000,normal[0],normal[1],normal[2]]
        tool_path.append(tool_step)

    print(np.array(tool_path))

    return np.array(tool_path)








tool_path = circle(10, [1.5,2,1])
print(tool_path)
