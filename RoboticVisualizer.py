import sys
import math
import numpy as np

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import (QApplication, QHBoxLayout, QOpenGLWidget, QSlider,
                             QWidget, QPushButton)

import OpenGL.GL as gl
import OpenGL.GLU as glu

from Machine import Machine, Axis
from ToolPathCreator import circle

class Window(QWidget):
    def __init__(self):
        super(Window, self).__init__()

        self.glWidget = GLWidget(self)
        self.glWidget.move(0,0)
        self.glWidget.resize(1920,1080)
        self.resize(1920,1080)

        self.setWindowTitle("5-Axis Simulator")

        self.machine = Machine()
        self.machine.base = Axis('base')
        self.machine.base.loadModel('base_frame.obj')
        self.machine.base.setColor(200,200,200)
        self.machine.base.setRelativePosition(1.5,-0.85,-1.15)

        x_axis = Axis('x_axis')
        x_axis.loadModel('x_axis.obj')
        x_axis.setColor(200,25,25)
        x_axis.defineMovement(type='linear', axis='x')
        x_axis.setRelativePosition(-1.5,4.55,0.35)

        y_axis = Axis('y_axis')
        y_axis.loadModel('y_axis.obj')
        y_axis.setColor(25,200,25)
        y_axis.defineMovement(type='linear', axis='z', negative=True)
        y_axis.setRelativePosition(0,0,3.125)

        z_axis = Axis('z_axis')
        z_axis.loadModel('z_axis.obj')
        z_axis.setColor(25,25,200)
        z_axis.defineMovement(type='linear', axis='y')
        z_axis.setRelativePosition(0,-0.15,0)


        a_axis = Axis('a_axis')
        a_axis.loadModel('a_axis.obj')
        a_axis.setColor(200,200,25)
        a_axis.defineMovement(type='rotation', axis='y')
        a_axis.setRelativePosition(0, -2.8, 0)

        b_axis = Axis('b_axis')
        b_axis.loadModel('b_axis_tool.obj')
        b_axis.setColor(200,25,200)
        b_axis.defineMovement(type='rotation', axis='z')
        b_axis.setRelativePosition(0, 0, 0.8)
        b_axis.setToolEndOffset(0,-0.75,0)


        self.machine.base.addChild(x_axis)
        self.machine.base.addChild(y_axis)
        x_axis.addChild(z_axis)

        z_axis.addChild(a_axis)
        a_axis.addChild(b_axis)

        self.machine.x_axis = x_axis
        self.machine.y_axis = y_axis
        self.machine.z_axis = z_axis
        self.machine.a_axis = a_axis
        self.machine.b_axis = b_axis

        self.machine.buildMachinState()

        x_axis.setAxisPositionInMM(0)
        y_axis.setAxisPositionInMM(0)
        z_axis.setAxisPositionInMM(0)

        a_axis.setAxisPositionInDeg(0)
        b_axis.setAxisPositionInDeg(0)

        self.machine.buildMachinState()
        self.machine.setToolPath(circle(500, [1.5,2,1]))
        self.machine.ready = True

        self.timer = QTimer()
        self.timer.timeout.connect(self.timer_step)
        self.timer.setInterval(1/60)
        self.timer.start()
        self.time_step = 0


    def timer_step(self):
        if self.machine.ready:
            self.time_step += 1
            #self.time_step = 25
            if self.time_step >= len(self.machine.tool_path):
                self.time_step = 0

            tool_step = self.machine.tool_path[int(self.time_step)]
            self.machine.calculateDesiredState(tool_step)
            self.machine.buildMachinState()
        else:
            pass
            #print('machine not ready')
        self.glWidget.update()






class GLWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        super(GLWidget, self).__init__(parent)

        format = QSurfaceFormat()
        format.setSamples(8)
        self.setFormat(format)

        self.xRot = 20*16
        self.yRot = -45*16
        self.zRot = 0
        self.xPos = 0
        self.yPos = 0
        self.zPos = 0

        self.lastPos = QPoint()

    def getOpenglInfo(self):
        info = """
            Vendor: {0}
            Renderer: {1}
            OpenGL Version: {2}
            Shader Version: {3}
        """.format(
            gl.glGetString(gl.GL_VENDOR),
            gl.glGetString(gl.GL_RENDERER),
            gl.glGetString(gl.GL_VERSION),
            gl.glGetString(gl.GL_SHADING_LANGUAGE_VERSION)
        )

        return info

    def minimumSizeHint(self):
        return QSize(50, 50)

    def sizeHint(self):
        return QSize(400, 400)

    def setXRotation(self, angle):
        angle = self.normalizeAngle(angle)
        if angle != self.xRot:
            self.xRot = angle

    def setYRotation(self, angle):
        angle = self.normalizeAngle(angle)
        if angle != self.yRot:
            self.yRot = angle

    def setZRotation(self, angle):
        angle = self.normalizeAngle(angle)
        if angle != self.zRot:
            self.zRot = angle

    def setXPosition(self, pos):
        if pos != self.xPos:
            self.xPos = pos

    def setYPosition(self, pos):
        if pos != self.yPos:
            self.yPos = pos

    def setZPosition(self, pos):
        if pos != self.zPos:
            self.zPos = pos

    def initializeGL(self):
        print(self.getOpenglInfo())
        self.setClearColor(QColor(255,255,255))
        self.axisIndicator = self.makeAxisIndicator(0.75, label=True)
        self.baseGrid = self.makeBaseGrid(10, coarse_spacing=1, fine_spacing=0.1)

        gl.glShadeModel(gl.GL_SMOOTH)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_CULL_FACE)
        gl.glEnable(gl.GL_MULTISAMPLE)
        #gl.glCullFace(gl.GL_FRONT)

    def paintGL(self):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glLoadIdentity()
        gl.glTranslated(self.xPos, self.yPos-2.0, self.zPos-12.5)
        gl.glRotated(self.xRot / 16.0, 1.0, 0.0, 0.0)
        gl.glRotated(self.yRot / 16.0, 0.0, 1.0, 0.0)
        gl.glRotated(self.zRot / 16.0, 0.0, 0.0, 1.0)
        gl.glCallList(self.baseGrid)
        gl.glCallList(self.axisIndicator)
        self.drawMachine(self.parent().machine)
        self.drawToolPath(self.parent().machine.tool_path)

    def resizeGL(self, width, height):
        side = min(width, height)
        if side < 0:
            return
        gl.glViewport((width) // 2, (height - side) // 2, side, side)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        glu.gluPerspective(45.0, (1920/1080), 0.0001, 10000.0)
        gl.glMatrixMode(gl.GL_MODELVIEW)

    def mousePressEvent(self, event):
        self.lastPos = event.pos()

    def mouseMoveEvent(self, event):
        dx = event.x() - self.lastPos.x()
        dy = event.y() - self.lastPos.y()
        if event.buttons() & Qt.LeftButton:
            self.setXRotation(self.xRot + 8 * dy)
            self.setYRotation(self.yRot + 8 * dx)
        elif event.buttons() & Qt.RightButton:
            self.setZPosition(self.zPos + 0.01 * dx)
        elif event.buttons() & Qt.MiddleButton:
            self.setXPosition(self.xPos + 0.003 * dx)
            self.setYPosition(self.yPos - 0.003 * dy)
        self.lastPos = event.pos()

    def makeAxisIndicator(self, size=1.0, label=False):
        genList = gl.glGenLists(1)
        gl.glNewList(genList, gl.GL_COMPILE)

        gl.glLineWidth(3.0)

        gl.glBegin(gl.GL_LINES)

        # draw base x-axis lines
        self.setColor(QColor(255, 0, 0))
        gl.glVertex3d(0, 0, 0)
        gl.glVertex3d(size, 0, 0)
        # draw 'X'
        gl.glVertex3d(1.05 * size, 0.1 * size, 0)
        gl.glVertex3d(1.2 * size, -0.1 * size, 0)
        gl.glVertex3d(1.05 * size, -0.1 * size, 0)
        gl.glVertex3d(1.2 * size, 0.1 * size, 0)

        # draw base y_axis-lines
        self.setColor(QColor(0, 255, 0))
        gl.glVertex3d(0, 0, 0)
        gl.glVertex3d(0, size, 0)
        # draw 'Y'
        gl.glVertex3d(0.075 * size, 1.3 * size, 0)
        gl.glVertex3d(0, 1.15 * size, 0)
        gl.glVertex3d(-0.075 * size, 1.3 * size, 0)
        gl.glVertex3d(0, 1.15 * size, 0)
        gl.glVertex3d(0, 1.05 * size, 0)
        gl.glVertex3d(0, 1.15 * size, 0)

        # draw base z_axis-lines
        self.setColor(QColor(0, 0, 255))
        gl.glVertex3d(0, 0, 0)
        gl.glVertex3d(0, 0, size)
        # draw 'Z'
        gl.glVertex3d(-0.075*size, 0.1*size, 1.05*size)
        gl.glVertex3d(0.075*size, 0.1*size, 1.05*size)
        gl.glVertex3d(-0.075 * size, -0.1 * size, 1.05 * size)
        gl.glVertex3d(0.075 * size, -0.1 * size, 1.05 * size)
        gl.glVertex3d(0.075 * size, 0.1 * size, 1.05 * size)
        gl.glVertex3d(-0.075 * size, -0.1 * size, 1.05 * size)

        gl.glEnd()
        gl.glLineWidth(1.0)
        gl.glEndList()
        return genList

    def makeBaseGrid(self, size, coarse_spacing=10.0, fine_spacing=1.0):
        genList = gl.glGenLists(1)
        gl.glNewList(genList, gl.GL_COMPILE)
        gl.glBegin(gl.GL_LINES)

        self.setColor(QColor(150, 150, 150))
        # draw base x-axis lines
        gl.glVertex3d(-size//2, 0, 0)
        gl.glVertex3d(size//2, 0, 0)
        # draw base z_axis-lines
        gl.glVertex3d(0, 0, size//2)
        gl.glVertex3d(0, 0, -size//2)

        for i in range(int((size/2)/coarse_spacing)):
            # draw coarse x-axis lines
            gl.glVertex3d(-size//2, 0, (i+1)*coarse_spacing)
            gl.glVertex3d(size//2, 0, (i+1)*coarse_spacing)
            gl.glVertex3d(-size//2, 0, -(i + 1) * coarse_spacing)
            gl.glVertex3d(size//2, 0, -(i + 1) * coarse_spacing)
            # draw coarse z-axis lines
            gl.glVertex3d((i + 1) * coarse_spacing,0,-size//2)
            gl.glVertex3d((i + 1) * coarse_spacing,0,size//2)
            gl.glVertex3d(-(i + 1) * coarse_spacing,0,-size//2)
            gl.glVertex3d(-(i + 1) * coarse_spacing,0,size//2)

        self.setColor(QColor(225, 225, 225))
        for i in range(int((size/2)/fine_spacing)):
            # draw coarse x-axis lines
            gl.glVertex3d(-size//2, 0, (i+1)*fine_spacing)
            gl.glVertex3d(size//2, 0, (i+1)*fine_spacing)
            gl.glVertex3d(-size//2, 0, -(i + 1) * fine_spacing)
            gl.glVertex3d(size//2, 0, -(i + 1) * fine_spacing)
            # draw coarse z-axis lines
            gl.glVertex3d((i + 1) * fine_spacing,0,-size//2)
            gl.glVertex3d((i + 1) * fine_spacing,0,size//2)
            gl.glVertex3d(-(i + 1) * fine_spacing,0,-size//2)
            gl.glVertex3d(-(i + 1) * fine_spacing,0,size//2)

        gl.glEnd()
        gl.glEndList()
        return genList

    def drawToolPath(self, tool_path):
        gl.glPushMatrix()
        offset = np.multiply(self.parent().machine.y_axis.axis_position, self.parent().machine.y_axis.linear_movement)
        gl.glTranslatef(offset[0], offset[1], offset[2])

        gl.glBegin(gl.GL_LINES)
        self.setColor(QColor(0, 0, 255))
        #print('drawing toolpath of length:', len(tool_path))
        for i in range(len(tool_path)-1):
            #draw tool path
            gl.glVertex3d(tool_path[i][0]/1000, tool_path[i][2]/1000, tool_path[i][1]/1000)
            gl.glVertex3d(tool_path[i+1][0]/1000, tool_path[i+1][2]/1000, tool_path[i+1][1]/1000)

        self.setColor(QColor(255, 0, 0))
        for i in range(len(tool_path)):
            #draw tool normal
            gl.glVertex3d(tool_path[i][0] / 1000, tool_path[i][2] / 1000, tool_path[i][1] / 1000)
            gl.glVertex3d(tool_path[i][0+3]+tool_path[i][0] / 1000, tool_path[i][2+3]+tool_path[i][2] / 1000, tool_path[i][1+3]+tool_path[i][1] / 1000)

        gl.glEnd()

        gl.glPopMatrix()

    def drawMachine(self, machine):
        gl.glPushMatrix()


        self.drawAxis(machine.base, 0)


        gl.glPopMatrix()

    def drawAxis(self, axis, recursion_level):
        #print('recursion_level:', recursion_level)
        #print('drawing', axis.name)

        position = np.add(axis.relative_translation, np.multiply(axis.axis_position, axis.linear_movement))
        gl.glTranslatef(position[0], position[1], position[2])

        #rotation = np.add(axis.relative_rotation, np.multiply(axis.axis_position, axis.rotational_movement))
        gl.glRotatef(axis.axis_position, axis.rotational_movement[0], axis.rotational_movement[1], axis.rotational_movement[2])

        gl.glBegin(gl.GL_QUADS)
        self.setColor(axis.color)
        for vertex in axis.getVertices():
            gl.glVertex3f(vertex[0], vertex[1], vertex[2])
        gl.glEnd()

        for child in axis.children:
            recursion_level += 1
            self.drawAxis(child, recursion_level)
            recursion_level -= 1

        gl.glTranslatef(-position[0], -position[1], -position[2])
        gl.glRotatef(axis.axis_position, -axis.rotational_movement[0], -axis.rotational_movement[1] ,-axis.rotational_movement[2])




    def normalizeAngle(self, angle):
        while angle < 0:
            angle += 360 * 16
        while angle > 360 * 16:
            angle -= 360 * 16
        return angle

    def setClearColor(self, c):
        gl.glClearColor(c.redF(), c.greenF(), c.blueF(), c.alphaF())

    def setColor(self, c):
        gl.glColor4f(c.redF(), c.greenF(), c.blueF(), c.alphaF())








if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())