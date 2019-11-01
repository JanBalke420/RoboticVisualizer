import numpy as np

def parsOBJ(path):
    print('loading', path)

    vertices = []
    texture_coordinates = []
    faces = []

    f = open(path, 'r')
    for line in f:
        if line[0] != '#':
            line_parts = line.replace('\n', '').split(' ')
            if line_parts[0] == 'v':
                vertex = [float(line_parts[1]), float(line_parts[2]), float(line_parts[3])]
                vertices.append(vertex)
            elif line_parts[0] == 'vt':
                tex_coord = [float(line_parts[1]), float(line_parts[2])]
                texture_coordinates.append(tex_coord)
            elif line_parts[0] == 'f' and len(line_parts) == 5:
                face = [int(line_parts[1].split('/')[0])-1, int(line_parts[2].split('/')[0])-1, int(line_parts[3].split('/')[0])-1, int(line_parts[4].split('/')[0])-1]
                faces.append(face)
    f.close()

    gl_vertices = []
    for face in faces:
        gl_vertices.append(vertices[face[0]])
        gl_vertices.append(vertices[face[1]])
        gl_vertices.append(vertices[face[2]])
        gl_vertices.append(vertices[face[3]])

    return np.asarray(gl_vertices)