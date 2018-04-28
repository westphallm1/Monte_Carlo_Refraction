import numpy as np
from matplotlib.patches import  Rectangle
LAMBDA0 = 400
LAMBDAf = 680
def wavelength_to_rgb(wavelength, gamma=0.8):
    '''This converts a given wavelength of light to an 
    approximate RGB color value. The wavelength must be given
    in nanometers in the range from 380 nm through 750 nm
    (789 THz through LAMBDA0 THz).

    Based on code by Dan Bruton
    http://www.physics.sfasu.edu/astro/color/spectra.html
    '''

    wavelength = float(wavelength)
    if wavelength >= 380 and wavelength <= 440:
        attenuation = 0.3 + 0.7 * (wavelength - 380) / (440 - 380)
        R = ((-(wavelength - 440) / (440 - 380)) * attenuation) ** gamma
        G = 0.0
        B = (1.0 * attenuation) ** gamma
    elif wavelength >= 440 and wavelength <= 490:
        R = 0.0
        G = ((wavelength - 440) / (490 - 440)) ** gamma
        B = 1.0
    elif wavelength >= 490 and wavelength <= 510:
        R = 0.0
        G = 1.0
        B = (-(wavelength - 510) / (510 - 490)) ** gamma
    elif wavelength >= 510 and wavelength <= 580:
        R = ((wavelength - 510) / (580 - 510)) ** gamma
        G = 1.0
        B = 0.0
    elif wavelength >= 580 and wavelength <= 645:
        R = 1.0
        G = (-(wavelength - 645) / (645 - 580)) ** gamma
        B = 0.0
    elif wavelength >= 645 and wavelength <= 750:
        attenuation = 0.3 + 0.7 * (750 - wavelength) / (750 - 645)
        R = (1.0 * attenuation) ** gamma
        G = 0.0
        B = 0.0
    else:
        R = 0.0
        G = 0.0
        B = 0.0
    return R,G,B

class Particle(object):
    def __init__(self,master,id_,x=0,y=0,theta=0,v=0,polarization = 1,
            wavelength=700.):
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
        self.wavelength = wavelength
        color = wavelength_to_rgb(self.wavelength)

        self._artist, = self.master.axes.plot(self.x,self.y,'o',color=color)
        self._gone = False

    def update(self):
        if not self._gone:
            self.move()
            self.delete_if_gone()
    

    def moveToNewLayer(self,layer,up=True):
        if up:
            new_sin = self.nprev*(np.sin(np.pi/2-self.theta))/self.n
        else:
            new_sin = self.nnext*(np.sin(np.pi/2-self.theta))/self.n
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
                self.v = self.v * self.nprev/self.n
            else:
                self.v = self.v * self.nnext/self.n
                self.theta *=-1
            self.vx = np.cos(self.theta)*self.v
            self.vy = np.sin(self.theta)*self.v
        else:
            self.reflect(layer,up)


    def getThetaIThetaF(self,layer,up=True):
        theta_i = np.pi/2 - self.theta
        if up:
            new_sin = self.nprev*(np.sin(theta_i))/self.n
            m = self.n/self.nprev
        else:
            new_sin = self.nnext*(np.sin(theta_i))/self.n
            m = self.n/self.nnext
        if np.abs(new_sin) > 1:
            theta_f = np.nan
        else:
            theta_f = np.arcsin(new_sin)

        return theta_i, theta_f, m

    def parallelPolarizedReflectivity(self,layer,up=True):
        theta_i, theta_f, m = self.getThetaIThetaF(layer,up)
        if np.isnan(theta_f):
            #total internal refraction
            return 1 
        cos_ti = np.cos(theta_i)
        cos_tf = np.cos(theta_f)
        if not up:
            cos_ti = np.abs(cos_ti)
        rp = ((cos_tf-m*cos_ti)/(cos_ti+m*cos_tf))**2
        return rp


    def perpendicularPolarizedReflectivity(self,layer,up=True):
        theta_i, theta_f, m = self.getThetaIThetaF(layer,up)
        if np.isnan(theta_f):
            #total internal refraction
            return 1 
        cos_ti = np.cos(theta_i)
        cos_tf = np.cos(theta_f)
        if not up:
            cos_ti = np.abs(cos_ti)
        rs = ((cos_ti-m*cos_tf)/(cos_tf+m*cos_ti))**2
        return rs

    def reflect(self, layer,up=True):
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

    def monteCarloRefract(self,layer,up=True):
        #TODO
        if self.polarization == 1:
            r = self.parallelPolarizedReflectivity(layer,up)
        else:
            r = self.perpendicularPolarizedReflectivity(layer,up)
        if np.random.rand() < r:
            self.reflect(layer,up)
            return True

    def checkForChangeLayers(self):
        for layer in self.master.layers:
            if self.enteringFromAbove(layer):
                self.n,self.nprev,self.nnext = \
                        layer.ns_for_lambda(self.wavelength)            
                if self.monteCarloRefract(layer):
                   pass 
                else:
                    self.moveToNewLayer(layer)
                break
            elif self.enteringFromBelow(layer):
                self.n,self.nprev,self.nnext = \
                        layer.ns_for_lambda(self.wavelength)            
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
    def __init__(self,n,y0,yf,nprev = 1,nnext = 1,dndlambda=1e-3):
        self.n = n
        self.nprev = nprev
        self.nnext = nnext
        self.color = (1./(n**2),1./(n**2),1./np.sqrt(n))
        self._artist = Rectangle((-1,yf),2,y0-yf,fill=True,facecolor=self.color)
        self.y0 = y0
        self.yf = yf
        #per nm
        self.dndlambda = dndlambda


    def set_master(self,master):
        self.master = master
        self.master.axes.add_artist(self._artist)

    def contains(self,y):
        return y >= self.yf and y < self.y0

    def ns_for_lambda(self,lambda_):
        def new_n(n):
            return max(1,n+(lambda_-LAMBDA0)*self.dndlambda)

        n = 1 if self.n == 1 else new_n(self.n)
        nprev = 1 if self.nprev == 1 else new_n(self.nprev) 
        nnext = 1 if self.nnext == 1 else new_n(self.nnext)
        return n,nprev,nnext

    def remove(self):
        self._artist.remove()


def buildLayers(ns,dndlambda=0.001):
    ys = np.linspace(0,-0.96,1+len(ns))
    layers = [Layer(1,1,0,1,ns[0],dndlambda)]
    for i,n in enumerate(ns):
        prev_n = 1 if i == 0 else ns[i-1]
        next_n = 1 if i == len(ns)-1 else ns[i+1]
        layers.append(Layer(n,ys[i],ys[i+1],prev_n,next_n,dndlambda))

    layers.append(Layer(1,-.96,-1,ns[-1],1,dndlambda))

    return layers

