import ObjParser
import numpy as np
from PyQt5.QtGui import QColor

class Machine:
    ready = False

    base = None
    axes = None

    x_axis = None
    y_axis = None
    z_axis = None
    a_axis = None
    b_axis = None

    tool_path = None

    def __init__(self):
        self.base = None
        self.axes = []
        self.tool_path = []

    def buildMachinState(self):
        #print('building machine state...')
        self.buildAxisState(self.base, np.array([0,0,0]), np.array([0,0,0]), 0)

    def buildAxisState(self, axis, parent_abs_trans, parent_abs_rot, recursion_level):
        position = np.add(axis.relative_translation, np.multiply(axis.axis_position, axis.linear_movement))
        axis.absolute_translation = np.add(position, parent_abs_trans)

        rotation = np.add(axis.relative_rotation, np.multiply(axis.axis_position, axis.rotational_movement))
        axis.absolute_rotation = np.add(rotation, parent_abs_rot)

        #print('|-' * recursion_level + axis.name, 'abs. pos:', axis.absolute_translation, 'abs. rot:', axis.absolute_rotation)

        for child in axis.children:
            recursion_level += 1
            self.buildAxisState(child, axis.absolute_translation, axis.absolute_rotation, recursion_level)
            recursion_level -= 1

    def setToolPath(self, tool_path):
        self.tool_path = tool_path

    def getAngle(self, vector):
        x = vector[0]
        y = vector[1]
        if x == 0.0 and y == 0.0:
            return 0.0
        elif x == 0.0:
            if y > 0.0:
                return 90.0
            elif y < 0.0:
                return 270.0
        elif y == 0.0:
            if x > 0.0:
                return 0.0
            elif x < 0.0:
                return 180.0
        else:
            angle = np.arctan(vector[1] / vector[0]) / (2 * np.pi) * 360
            if x < 0.0:
                return 180 + angle
            elif y < 0.0:
                return 360 + angle
            else:
                return angle

    def rotate3D(self, vector, angle, axis):
        angle = np.deg2rad(angle)
        rot_x = np.array([[1.0, 0.0, 0.0], [0.0, np.cos(angle), np.sin(angle)], [0.0, -np.sin(angle), np.cos(angle)]])
        rot_y = np.array([[np.cos(angle), 0.0, -np.sin(angle)], [0.0, 1.0, 0.0], [np.sin(angle), 0.0, np.cos(angle)]])
        rot_z = np.array([[np.cos(angle), np.sin(angle), 0.0], [-np.sin(angle), np.cos(angle), 0.0], [0.0, 0.0, 1.0]])

        final_rot = np.add(np.add(np.multiply(rot_x, axis[0]), np.multiply(rot_y, axis[1])), np.multiply(rot_z, axis[2]))

        final_vec = np.matmul(final_rot, vector)
        return final_vec


    def calculateDesiredState(self, tool_step):
        # 3-axis example
        des_x = tool_step[0]
        des_y = tool_step[1]
        des_z = tool_step[2]

        des_norm_x = tool_step[3]
        des_norm_y = tool_step[4]
        des_norm_z = tool_step[5]

        angle_around_z = self.getAngle([des_norm_x, -des_norm_y])
        des_a = angle_around_z
        self.a_axis.setAxisPositionInDeg(des_a)

        de_rotated = self.rotate3D([des_norm_x, des_norm_y, des_norm_z], -angle_around_z, [0,0,1])
        angle_around_y = self.getAngle([de_rotated[0], de_rotated[2]])
        des_b = angle_around_y - 90
        self.b_axis.setAxisPositionInDeg(des_b)



        # compensate xyz translation for ab rotation - WORKS!!!
        tool_pos_without_rot = np.add(self.b_axis.relative_translation, self.b_axis.tool_end_offset)
        tool_pos_without_rot = [tool_pos_without_rot[0], tool_pos_without_rot[2], tool_pos_without_rot[1]]

        tool_pos_with_rot = self.rotate3D(tool_pos_without_rot, des_b, [0, 1, 0])
        tool_pos_with_rot = self.rotate3D(tool_pos_with_rot, des_a, [0, 0, 1])
        tool_pos_with_rot = np.add(np.array(tool_pos_with_rot), -np.array(tool_pos_without_rot))

        #print(tool_pos_without_rot, tool_pos_with_rot)

        self.x_axis.setAxisPositionInMM(des_x-tool_pos_with_rot[0]*1000)
        self.y_axis.setAxisPositionInMM(des_y-tool_pos_with_rot[1]*1000)
        self.z_axis.setAxisPositionInMM(des_z-tool_pos_with_rot[2]*1000)










class Axis:
    name = ''
    color = None
    children = None

    raw_vertices = None

    relative_translation = None
    absolute_translation = None

    relative_rotation = None
    absolute_rotation = None

    linear_movement = None
    rotational_movement = None

    movement_type = ''
    axis_position = 0.0
    #end_stop = 0.0

    tool_end_offset = None

    def __init__(self, name):
        self.name = name
        self.color = QColor(0,0,0)
        self.children = []
        self.raw_vertices = []
        self.relative_translation = np.array([0.0, 0.0, 0.0])
        self.absolute_translation = np.array([0.0, 0.0, 0.0])
        self.relative_rotation = np.array([0.0, 0.0, 0.0])
        self.absolute_rotation = np.array([0.0, 0.0, 0.0])
        self.linear_movement = np.array([0.0, 0.0, 0.0])
        self.rotational_movement = np.array([0.0, 0.0, 0.0])
        self.tool_end_offset = np.array([0.0, 0.0, 0.0])
        self.defineMovement()
        self.loadModel('cube.obj')


    def loadModel(self, path):
        self.raw_vertices = ObjParser.parsOBJ(path)

    def getVertices(self):
        return self.raw_vertices

    def setColor(self,r,g,b):
        self.color = QColor(r,g,b)

    def setRelativePosition(self,x,y,z):
        self.relative_translation = np.array([x,y,z])

    def setToolEndOffset(self,x,y,z):
        self.tool_end_offset = np.array([x,y,z])

    def addChild(self, child):
        self.children.append(child)

    def defineMovement(self, type='liner', axis='x', negative=False):
        self.movement_type = type
        if axis == 'x':
            movement_axis = np.array([1.0, 0.0, 0.0])
        elif axis == 'y':
            movement_axis = np.array([0.0, 1.0, 0.0])
        elif axis == 'z':
            movement_axis = np.array([0.0, 0.0, 1.0])

        if negative:
            movement_axis = np.multiply(movement_axis, -1)

        if type == 'linear':
            self.linear_movement = movement_axis
        elif type == 'rotation':
            self.rotational_movement = movement_axis

    def setAxisPositionInMM(self, value):
        self.axis_position = value/1000

    def setAxisPositionInDeg(self, value):
        self.axis_position = value



if __name__ == '__main__':
    machine = Machine()
    machine.base = Axis('base')

    x_axis = Axis('x_axis')
    x_axis.defineMovement(type='linear', axis='x')
    y_axis = Axis('y_axis')
    y_axis.defineMovement(type='linear', axis='y')
    z_axis = Axis('z_axis')
    z_axis.defineMovement(type='linear', axis='z')

    a_axis = Axis('a_axis')
    a_axis.defineMovement(type='rotation', axis='z')
    b_axis = Axis('b_axis')
    b_axis.defineMovement(type='rotation', axis='y')


    machine.base.addChild(x_axis)
    x_axis.addChild(y_axis)
    y_axis.addChild(z_axis)

    z_axis.addChild(a_axis)
    a_axis.addChild(b_axis)

    machine.buildMachinState()
    print('')

    x_axis.setAxisPositionInMM(500)
    y_axis.setAxisPositionInMM(300)
    z_axis.setAxisPositionInMM(400)

    a_axis.setAxisPositionInDeg(180)
    b_axis.setAxisPositionInDeg(180)

    machine.buildMachinState()