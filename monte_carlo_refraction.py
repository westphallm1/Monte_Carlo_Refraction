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

progname = os.path.basename(sys.argv[0])
progversion = "0.1"

class Particle(object):
    def __init__(self,master,id_,x=0,y=0,theta=0,v=0,polarization = 1):
        self._id = id_
        self.master = master
        self.x = x
        self.y = y
        self.theta = theta
        self.v = v
        self.vx = np.cos(theta)*v
        self.vy = np.sin(theta)*v
        self.bounces = 0
        self.polarization = polarization

        self._artist, = self.master.axes.plot(self.x,self.y,'ro')
        self._gone = False

    def update(self):
        if not self._gone:
            self.move()
            self.delete_if_gone()
    

    def moveToNewLayer(self,layer,up=True):
        if up:
            new_sin = layer.nprev*(np.sin(np.pi/2-self.theta))/layer.n
        else:
            new_sin = layer.nnext*(np.sin(np.pi/2-self.theta))/layer.n
        if (-1 < new_sin) and (new_sin < 1):
            #move right to the boundry so we don't double count it
            if up:
                pct_move = (layer.y0-self.y)/self.vy
                assert pct_move > 0 and pct_move < 1
            else:
                pct_move = (layer.yf-self.y)/self.vy
                assert pct_move > 0 and pct_move < 1
            self.y += self.vy*pct_move
            self.x += self.vx*pct_move
            self.theta = np.pi/2-np.arcsin(new_sin)
            if up:
                self.v = self.v * layer.nprev/layer.n
            else:
                self.v = self.v * layer.nnext/layer.n
                self.theta *=-1
            self.vx = np.cos(self.theta)*self.v
            self.vy = np.sin(self.theta)*self.v
        else:
            self._delete_self()


    def getThetaIThetaF(self,layer,up=True):
        theta_i = np.pi/2 - self.theta
        if up:
            new_sin = layer.nprev*(np.sin(theta_i))/layer.n
            m = layer.n/layer.nprev
        else:
            new_sin = layer.nnext*(np.sin(theta_i))/layer.n
            m = layer.n/layer.nnext
        theta_f = np.arcsin(new_sin)

        return theta_i, theta_f, m

    def parallelPolarizedReflectivity(self,layer,up=True):
        theta_i, theta_f, m = self.getThetaIThetaF(layer,up)
        cos_ti = np.cos(theta_i)
        cos_tf = np.cos(theta_f)
        if not up:
            cos_ti = np.abs(cos_ti)
        rp = ((cos_tf-m*cos_ti)/(cos_ti+m*cos_tf))**2
        return rp


    def perpendicularPolarizedReflectivity(self,layer,up=True):
        theta_i, theta_f, m = self.getThetaIThetaF(layer,up)
        cos_ti = np.cos(theta_i)
        cos_tf = np.cos(theta_f)
        if not up:
            cos_ti = np.abs(cos_ti)
        rs = ((cos_ti-m*cos_tf)/(cos_tf+m*cos_ti))**2
        return rs

    def monteCarloRefract(self,layer,up=True):
        #TODO
        if self.polarization == 1:
            r = self.parallelPolarizedReflectivity(layer,up)
        else:
            r = self.perpendicularPolarizedReflectivity(layer,up)
        if np.random.rand() < r:
            self.bounces+=1
            if up:
                pct_move = (layer.y0-self.y)/self.vy
            else:
                pct_move = -(self.y-layer.yf)/self.vy
            self.y += self.vy*pct_move
            self.x += self.vx*pct_move
            self.theta = -self.theta
            self.vx = np.cos(self.theta)*self.v
            self.vy = np.sin(self.theta)*self.v
            return True

    def checkForChangeLayers(self):
        for layer in self.master.layers:
            if self.enteringFromAbove(layer):
                if self.monteCarloRefract(layer):
                   pass 
                else:
                    self.moveToNewLayer(layer)
                break
            elif self.enteringFromBelow(layer):
                if self.monteCarloRefract(layer,up=False):
                   pass 
                else:
                    self.moveToNewLayer(layer,up=False)
                break


    def enteringFromAbove(self,layer):
        return (self.vy < 0)and(self.y > layer.y0)and(self.y+self.vy < layer.y0)

    def enteringFromBelow(self,layer):
        return (self.vy > 0)and(self.y < layer.yf)and(self.y+self.vy > layer.yf)

    def move(self):
        self.checkForChangeLayers()
        self.x+=self.vx
        self.y+=self.vy
        self._artist.set_xdata(self.x)
        self._artist.set_ydata(self.y)

    def _delete_self(self):
        if not self._gone:
            self._gone = True
            self._artist.remove()
            self.master.remove_particle(self._id)

    def delete_if_gone(self):
        if(self.x > self.master.axes.get_xlim()[1] or 
           self.x < self.master.axes.get_xlim()[0] or 
           self.y > self.master.axes.get_ylim()[1] or
           self.y < self.master.axes.get_ylim()[0]   ):
            self._delete_self()


class Layer(object):
    def __init__(self,n,y0,yf,nprev = 1,nnext = 1):
        self.n = n
        self.nprev = nprev
        self.nnext = nnext
        self.color = (1./(n**2),1./(n**2),1./np.sqrt(n))
        self._artist = Rectangle((-1,yf),2,y0-yf,fill=True,facecolor=self.color)
        self.y0 = y0
        self.yf = yf

    def set_master(self,master):
        self.master = master
        self.master.axes.add_artist(self._artist)

    def remove(self):
        self._artist.remove()


def buildLayers(ns):
    ys = np.linspace(0,-0.96,1+len(ns))
    layers = [Layer(1,1,0,1,ns[0])]
    for i,n in enumerate(ns):
        prev_n = 1 if i == 0 else ns[i-1]
        next_n = 1 if i == len(ns)-1 else ns[i+1]
        layers.append(Layer(n,ys[i],ys[i+1],prev_n,next_n))

    layers.append(Layer(1,-.96,-1,ns[-1],1))

    return layers

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


        def onclick(event):
            self.isclicked = True
            if event.xdata is not None:
                self.move_source(event.xdata)

        def onmove(event):
            if self.isclicked and event.xdata is not None:
                self.move_source(event.xdata)
        def onmouseup(event):
            self.isclicked = False

        self.axes.xaxis.set_ticks([])
        self.axes.yaxis.set_ticks([])
        self.mpl_connect('button_press_event',onclick)
        self.mpl_connect('button_release_event',onmouseup)
        self.mpl_connect('motion_notify_event',onmove)


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

    def move_source(self,x):
        #edge case behaviour is not strictly correct, disable it
        if x > .999:
            x = 0.999
        if x < -.999:
            x = -.999
        if(self._source_box):
            self._source_box.remove()

        theta = np.arccos(x)
        self.theta = theta
        y = np.sin(theta)
        sin_t = y
        cos_t = x
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
        self.moving_artists[self._ids] = (Particle(self,self._ids,x,y,theta,v,
            polarization=self._ids%2))
        self._ids += 1

    def add_particle_at_source(self,v=0):
        self.add_particle(self._source_x,self._source_y,self.theta,-v)


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
        menu_l.addStretch(1)
        l.addLayout(menu_l)

        self.dc.add_source()
        self.add_layer()



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
