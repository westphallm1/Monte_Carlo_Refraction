# embedding_in_qt5.py --- Simple Qt5 application embedding matplotlib canvases
#
# Copyright (C) 2005 Florent Rougon
#               2006 Darren Dale
#               2015 Jens H Nielsen
#
# This file is an example program for matplotlib. It may be used and
# modified with no restriction; raw copies as well as modified versions
# may be distributed without limitation.

from __future__ import unicode_literals
import sys
import os
import random
import numpy as np
import matplotlib
# Make sure that we are using QT5
matplotlib.use('Qt5Agg')
from PyQt5 import QtCore, QtWidgets

from numpy import arange, sin, pi
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.patches import Polygon, Rectangle
from artists import Layer, buildLayers, Particle

progname = os.path.basename(sys.argv[0])
progversion = "0.1"


class MyMplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

    def __init__(self, parent=None, width=8, height=8, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.fig = fig
        self.canvas = fig.canvas
        self.axes = fig.add_subplot(111)
        self.axes.set_xlim(-1,1)
        self.axes.set_ylim(-1,1)
        self.axes.set_title("Monte Carlo Refraction")
        
        self.compute_initial_figure()

        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def compute_initial_figure(self):
        pass


class MyDynamicMplCanvas(MyMplCanvas):
    """A canvas that updates itself every second with a new plot."""

    COLORS = ['red','orange','yellow','green','blue','purple']
    def __init__(self, *args, **kwargs):
        MyMplCanvas.__init__(self, *args, **kwargs)
        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.update_figure)
        timer.start(32)
        self._ids = 0
        self._to_delete = set()
        self.moving_artists = {}
        self._cleanup = 20 #only check for cleanup every 1/n frames
        self._frame = 0
        self.isclicked = False
        self.n0 = 1
        self.last_x = 1
        self.isrotating = False
        self.framesrotating = 0
        self.mode='circle'



        def onclick(event):
            if self.mode=='circle':
                self.circlemove(event)
            elif self.mode=='free':
                self.freemove(event)

        def onmove(event):
            if self.mode=='circle':
                self.circledrag(event)
            elif self.mode=='free':
                self.freedrag(event)

        def onmouseup(event):
            self.isclicked = False
            self.isrotating = False

        self.axes.xaxis.set_ticks([])
        self.axes.yaxis.set_ticks([])
        self.mpl_connect('button_press_event',onclick)
        self.mpl_connect('button_release_event',onmouseup)
        self.mpl_connect('motion_notify_event',onmove)


    def freemove(self,event):
        self.framesrotating = 0
        if event.button == 1:
            self.isrotating = -1
            self.isclicked = True
        else:
            self.isrotating = 1

    def circlemove(self,event):
        if event.button == 1:
            self.isclicked = True
            if event.xdata is not None:
                self.move_source(event.xdata,event.ydata)

    def freedrag(self,event):
        self.isrotating = False
        if event.button == 1:
            if self.isclicked and event.xdata is not None:
                self.free_move_source(event.xdata,event.ydata)
                self.last_x = event.xdata

    def circledrag(self,event):
        self.isrotating = False
        if event.button == 1:
            if self.isclicked and event.xdata is not None:
                self.move_source(event.xdata,event.ydata)
                self.last_x = event.xdata
            elif self.isclicked:
                self.move_source(np.sign(self.last_x),0)


    def setCircleMode(self):
        self.mode = 'circle'
        self.move_source(self._source_x,self._source_y)

    def setFreeMode(self):
        self.mode = 'free'

    def set_reflection_counts(self,reflection_counts):
        self.reflection_counts = reflection_counts

    def setLayers(self,layers):
        self.layers = layers
        for layer in layers:
            layer.set_master(self)

        self.draw()

    def set_master(self,master):
        self.master = master

    def add_source(self):
        self.source_dx = .08
        self.source_dy = .05
        self._source_box = None
        self.move_source(np.cos(np.pi/4))
        #source lies along an arc from (-1,0) to (0,1) to (1,0)

    def set_source_angle(self,x,y,theta,is_circular=False):
        if(self._source_box):
            self._source_box.remove()
        sin_t = np.sin(theta)

        #what a clusterfuck
        if y < 0 and is_circular:
            sin_t = -sin_t
        cos_t = np.cos(theta)
        self._source_x = x
        self._source_y = y
        xprime1 = x+self.source_dx*cos_t
        yprime1 = y+self.source_dx*sin_t
        xprime2 = x-self.source_dx*cos_t
        yprime2 = y-self.source_dx*sin_t

        x1 = xprime1-self.source_dy*sin_t
        y1 = yprime1+self.source_dy*cos_t

        x2 = xprime2-self.source_dy*sin_t
        y2 = yprime2+self.source_dy*cos_t

        x3 = xprime2+self.source_dy*sin_t
        y3 = yprime2-self.source_dy*cos_t

        x4 = xprime1+self.source_dy*sin_t
        y4 = yprime1-self.source_dy*cos_t

        xs = [x1,x2,x3,x4]
        ys = [y1,y2,y3,y4]

        self._source_box = Polygon(np.column_stack([xs,ys]),fill=True,
                facecolor=(.5,.5,.5))
        self.axes.add_artist(self._source_box)
        self.master.update_angle(int(np.rad2deg(np.pi/2 - self.theta)))


    def free_move_source(self,x,y):
        self.set_source_angle(x,y,self.theta)

    def rotate_source(self,theta):
        self.theta=theta

        self.set_source_angle(self._source_x,self._source_y,self.theta)

    def move_source(self,x,event_y=1):
        #edge case behaviour is not strictly correct, disable it
        if x > 1:
            x = 1
        if x < -1:
            x = -1

        theta = np.arccos(x)
        self.theta = theta
        y = np.sin(theta)
        if event_y < 0:
            self.theta = -self.theta
            y = -y
            for layer in self.layers:
                if layer.contains(y):
                    self.n0 = layer.n
                    break
        self.set_source_angle(x,y,theta,True)
        #self.draw()


    def reset(self):
        for particle in self.moving_artists:
            self.moving_artists[particle]._delete_self()

        self._remove_particles()

        for layer in self.layers:
            layer.remove()
        self.layers = []
        self.draw()


    def compute_initial_figure(self):
        pass 

    def update_figure(self):
        # Build a list of 4 random integers between 0 and 10 (both inclusive)
        self._frame+=1
        for key in self.moving_artists:
            self.moving_artists[key].update()
        if self._frame%self._cleanup == 0:
            self._remove_particles()

        if self.isrotating:
            self.framesrotating += 1
            speed = (self.framesrotating*np.pi/360 if self.framesrotating < 24 
                    else np.pi/15)
            self.rotate_source((self.theta+self.isrotating*speed)%(2*np.pi))
        self.draw()


    def remove_particle(self,id_):
        self._to_delete.add(id_)

    def _remove_particles(self):
        for key in self._to_delete:
            particle = self.moving_artists.pop(key)
            if particle.bounces >= len(self.reflection_counts)-1:
                key = str(len(self.reflection_counts)-1)+"+"
            else:
                key = str(particle.bounces)
                self.reflection_counts[key]+=1
        self._to_delete = set()

    def add_particle(self,x=0,y=0,theta=0,v=0):
        color = self.COLORS[np.random.randint(0,len(self.COLORS))]
        self.moving_artists[self._ids] = (Particle(self,self._ids,x,y,theta,v,
            polarization=self._ids%2, color=color))
        self._ids += 1

    def add_particle_at_source(self,v=0):
        self.add_particle(self._source_x,self._source_y,self.theta,-v/self.n0)


class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("Monte Carlo Refraction")

        self.file_menu = QtWidgets.QMenu('&File', self)
        self.file_menu.addAction('&Quit', self.fileQuit,
                                 QtCore.Qt.CTRL + QtCore.Qt.Key_Q)
        self.menuBar().addMenu(self.file_menu)

        self.reflection_counts = {
                "0":0,
                "1":0,
                "2":0,
                "3":0,
                "4+":0
        }
        self.help_menu = QtWidgets.QMenu('&Help', self)
        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.help_menu)

        self.help_menu.addAction('&About', self.about)

        self.main_widget = QtWidgets.QWidget(self)

        self.setup_canvas()

        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)

        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.create_particle)
        timer.start(16)

        timer2 = QtCore.QTimer(self)
        timer2.timeout.connect(self.update_counts)
        timer2.start(500)


    def setup_canvas(self):
        l = QtWidgets.QHBoxLayout(self.main_widget)
        self.dc = MyDynamicMplCanvas(self.main_widget, dpi=100)
        self.dc.set_reflection_counts(self.reflection_counts)
        self.dc.set_master(self)

        l.addWidget(self.dc)

        layers = buildLayers([1.33])
        self.dc.setLayers(layers)

        self.setup_menu(l)
        self.dc.add_source()
        self.add_layer()


    def setup_menu(self,l):
        menu_l = QtWidgets.QVBoxLayout()

        self.angle_label = QtWidgets.QLabel(self.main_widget,
                text="Initial Angle: ")
        menu_l.addWidget(self.angle_label)

        menu_l.addWidget(QtWidgets.QLabel(self.main_widget,
            text="Reflection Counts:"))

        self.count_labels = {}
        for key in self.reflection_counts:
            self.count_labels[key] = QtWidgets.QLabel(self.main_widget,
                    text=key+": 0")
            menu_l.addWidget(self.count_labels[key])


        label_l = QtWidgets.QHBoxLayout()
        label_l.addWidget(QtWidgets.QLabel(self.main_widget,
            text="N = "))
        label_l.addStretch(1)
        plusbutton = QtWidgets.QToolButton(text="+")
        plusbutton.clicked.connect(self.add_layer)
        minusbutton = QtWidgets.QToolButton(text="-")
        minusbutton.clicked.connect(self.remove_layer)
        updatebutton = QtWidgets.QToolButton(text="Update")
        updatebutton.clicked.connect(self.update_layers)
        label_l.addWidget(plusbutton)
        label_l.addWidget(minusbutton)
        label_l.addWidget(updatebutton)
        menu_l.addLayout(label_l)
        self.layer_list = QtWidgets.QListWidget(self.main_widget)
        menu_l.addWidget(self.layer_list)


        radioBox = QtWidgets.QVBoxLayout()
        radioBox.addWidget(QtWidgets.QLabel("Click and Drag:"))
        circlebtn = QtWidgets.QRadioButton("Snap to Circle")
        circlebtn.setChecked(True)
        circlebtn.toggled.connect(lambda:self.movementRadios(circlebtn))
        freebtn = QtWidgets.QRadioButton("Free Movement")
        freebtn.toggled.connect(lambda:self.movementRadios(freebtn))
        radioBox.addWidget(circlebtn)
        radioBox.addWidget(freebtn)
        radioBox.addWidget(QtWidgets.QLabel("Auto Move:"))
        orbitbtn = QtWidgets.QRadioButton("Orbit Perimeter")
        orbitbtn.toggled.connect(lambda:self.movementRadios(orbitbtn))
        spinbtn = QtWidgets.QRadioButton("Spin in Place")
        spinbtn.toggled.connect(lambda:self.movementRadios(spinbtn))
        radioBox.addWidget(orbitbtn)
        radioBox.addWidget(spinbtn)

        menu_l.addLayout(radioBox)
        menu_l.addStretch(1)
        l.addLayout(menu_l)
    
    def movementRadios(self,btn):
        if btn.isChecked():
            text = btn.text()
            if text == "Free Movement":
                self.dc.setFreeMode()
            elif text == "Snap to Circle":
                self.dc.setCircleMode()

    def add_layer(self):
        item = QtWidgets.QListWidgetItem("1.33",parent=self.layer_list)
        item.setFlags(QtCore.Qt.ItemIsEditable|QtCore.Qt.ItemIsSelectable|
                QtCore.Qt.ItemIsEnabled)
        self.layer_list.addItem(item)

    def remove_layer(self):
        to_remove = self.layer_list.selectedItems()
        if len(to_remove) == 0 and self.layer_list.count() > 0:
            to_remove.append(self.layer_list.item(
                self.layer_list.count()-1))
        for item in to_remove:
            idx = self.layer_list.indexFromItem(item)
            self.layer_list.takeItem(idx.row())

    def update_layers(self):
        layers = []
        for i in range(self.layer_list.count()):
            item = self.layer_list.item(i)
            layers.append(float(item.text()))
        self.dc.reset()
        layers = buildLayers(layers)
        self.dc.setLayers(layers)
        self.dc.move_source(np.cos(self.dc.theta))
        for key in self.reflection_counts:
            self.reflection_counts[key] = 0

        self.dc.draw()

    def update_angle(self,angle):
        self.angle_label.setText("Initial Angle: {}°".format(int(angle)))

    def update_counts(self):
        sum_ = 0.
        for key in self.reflection_counts:
            sum_ += self.reflection_counts[key]
        if sum_ == 0: sum_ = 1

        for key in self.reflection_counts:
            count = self.reflection_counts[key]
            pct = "%.2f"%(100.*count/sum_)
            self.count_labels[key].setText(
                    "{}: {} ({}%)".format(key,count,pct))

    def create_particle(self):
        self.dc.add_particle_at_source(0.04)

    def fileQuit(self):
        self.close()

    def closeEvent(self, ce):
        self.fileQuit()

    def about(self):
        QtWidgets.QMessageBox.about(self, "About",
                                    """Refraction Demo, based off of the embedding_in_qt5.py example
Copyright 2005 Florent Rougon, 2006 Darren Dale, 2015 Jens H Nielsen

This program is a simple example of a Qt5 application embedding matplotlib
canvases.

It may be used and modified with no restriction; raw copies as well as
modified versions may be distributed without limitation.

This is modified from the embedding in qt4 example to show the difference
between qt4 and qt5"""
                                )


qApp = QtWidgets.QApplication(sys.argv)

aw = ApplicationWindow()
aw.setWindowTitle("%s" % progname)
aw.show()
sys.exit(qApp.exec_())
