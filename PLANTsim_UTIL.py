#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 19 09:29:29 2021

@author: glbramalho@gmail.com - Geraldo Ramalho
"""

import csv
from numpy import random, exp
from colorama import Fore as fg, Back as bg, Style as st


###################################### CONTROLLERS
#
######################################
from CTRL_PID import PID # plant PID controls plant actuators

###################################### SCREEN/FORMATING UTILS
#
#####################################  
def clear_screen():
    print(chr(27) + "[2J")

def hm(seg):
    """ simple format hour:minute
    """ 
    return '%02d:%02d'%(seg/60, seg % 60)

class Status_Bar(object):
    """ display formated status bar
    """     
    def __init__(self):
        self._status = []
        self._WIDTH = 100

    def add(self,section='',data=''):
        self._status.append((section,data))

    def clear(self):
        self._status = []

    def __call__(self):
        bar_color = bg.WHITE+fg.BLUE
        line = 0
        for sec,sts in  self._status:
            color = bar_color
            if sec in ['title']:
                color = bg.WHITE+fg.BLACK
            elif sec in ['warning']:
                color = bg.YELLOW+st.BRIGHT+fg.RED
            elif sec in ['comm']:
                color = bg.BLUE+fg.RESET
            elif sec in ['txrx']:
                color = bg.GREEN+st.BRIGHT+fg.BLACK
            elif sec in ['info']:
                color = bg.CYAN+fg.RESET
            elif sec in ['prg']:
                color = bg.BLUE+fg.WHITE
            elif sec in ['debug']:
                color = bg.WHITE+st.BRIGHT+fg.MAGENTA
                
            print(color,sts,st.RESET_ALL,end='')
            print(bar_color+'|',end='')
            line += len(sts)+3
    
        print(bar_color+' '*(self._WIDTH-line)+st.RESET_ALL)
        self.clear()
    

################################### MATH
##
###################################
def diff(limits):
    """ compute the difference between two values or array of values
        return a value if input is a two elements array or tuple
        return a list of differences if input is a more than two elements array
    """ 
    try:
        d = [ a[1]-a[0] for a in zip(limits[:-1],limits[1:])]
    except:
        raise Exception('+++ DIFF invalid values')
    if d:
        return sum(d)/len(d)
    else:
        return 0

def noise(signal, snr):
    """ simple noise function
    """ 
    return signal + random.randn()*snr

################################### CONFIG 
##
###################################
def load_config(file_name):
    """ loads INI file
    """ 
    CFG = {}
    try:
        # CSV file with header
        with open(file_name) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=' ')
            for row in csv_reader:
                if row and  row[0] not in '# ':
                    if len(row)>1:
                        if row[1].upper() in [ 'TRUE','FALSE']: row[1] = row[1].capitalize()
                        try:
                            CFG[row[0]] = eval(row[1])
                        except:
                            CFG[row[0]] = row[1]
    except:
        raise Exception('*** Unable to read .ini file.')
    return CFG


################################### SIMULATED systems
##
###################################
# any system must have the same interface (see update method)

def ph_mix():
    return None

def temp_mix(volume=[0,0],temp=[25,25],liquid=['water','water']):    
    """heat (c) = specific heat capacity Kj/(Kg*K); density (rho) = grams/cm3
    Water 4.18 
    Ethanol 2.43
    Air 1.00
    Water Vapor 2.08
    Resin 1.11
    input: volume = [volume1,volume2]
           temp = [temp1,temp2]
           liquid = [liquid1,liquid2]
    output: temp_result
    """
    # LIQUID paramseters at 25oC: # c:Kj/(Kg*K), rho:grams/cm3
    LIQUIDS = {'water':(4.18,1),
              'ethanol':(2.43,1),
              'vapor':(2.08,1),
              'air':(1.00,1),
              'resin':(1.11,0.561)
              }
            
    if len(liquid) != 2 or len(volume) != len(liquid) or len(temp) != len(liquid): 
        raise Exception('TEMPERATURE_MIX: inform at least 2 liquids!')
        
    heat = [] # Kj/(Kg*K)
    mass=[] # grams/cm3
    density = []
    for liq,vol in zip(liquid,volume):
        c,rho = LIQUIDS[liq.lower()]
        heat.append(c)
        density.append(rho)
        mass.append(rho*(vol/1000))
        
    m1,m2 = mass
    c1,c2 = heat 
    T1,T2 = temp
    total = ( m1*c1 + m2*c2 )
    if total < 0.0001:
        return 0
    return ( m1*c1*T1 + m2*c2*T2 ) / total


# reactor -----------------------------------------------------------
from scipy.integrate import odeint
class reactor(object):
    """ NOT USED
    TODO reactor
    """ 
    
    def __init__(self):
        self.pv = 0.1
        self.limits = None
        self.noise = 0
        self.loss = 0
        self.time = 0
        
        self.Ea  = 72750     # activation energy J/gmol
        self.R   = 8.314     # gas constant J/gmol/K
        self.k0  = 7.2e10    # Arrhenius rate constant 1/min
        self.V   = 100.0     # Volume [L]
        self.rho = 1000.0    # Density [g/L]
        self.Cp  = 0.239     # Heat capacity [J/g/K]
        self.dHr = -5.0e4    # Enthalpy of reaction [J/mol]
        self.UA  = 5.0e4     # Heat transfer [J/min/K]
        self.q = 100.0       # Flowrate [L/min]
        self.Cf = 1.0        # Inlet feed concentration [mol/L]
        self.Tf  = 300.0     # Inlet feed temperature [K]
        self.C0 = 0.5        # Initial concentration [mol/L]
        self.T0  = 350.0;    # Initial temperature [K]
        self.Tcf = 300.0     # Coolant feed temperature [K]
        self.qc = 50.0       # Nominal coolant flowrate [L/min]
        self.Vc = 20.0       # Cooling jacket volume

    def mix_pv(self,pv,dt):
        self.pv = (self.pv+pv*dt)/(1+dt)
    
    def __call__(self, inlet=True, mv=0, dt=0, var=None):
        return self.update(inlet, mv, dt, var)
    
    def __repr__(self):
        return (
            '{self.__class__.__name__}('
            'pv={self.pv!r}, limits={self.limits!r}, noise={self.noise!r}, '
            'loss={self.loss!r}'
            ')'
        ).format(self=self)
    
    # Arrhenius rate expression
    def k(self,T):
        return self.k0*exp(-self.Ea/self.R/T)
    
    def deriv(self,X,t):
        C,T,Tc = X
        dC = (self.q/self.V)*(self.Cf - C) - self.k(T)*C
        dT = (self.q/self.V)*(self.Tf - T) + (-self.dHr/self.rho/self.Cp)*self.k(T)*C + (self.UA/self.V/self.rho/self.Cp)*(Tc - T)
        dTc = (self.qc/self.Vc)*(self.Tcf - Tc) + (self.UA/self.Vc/self.rho/self.Cp)*(T - Tc)
        return [dC,dT,dTc]

    def init(self, time, C0, T0, Tcf): #, limits=None, loss=None, noise=None):
        self.time = time
        self.C0 = C0
        self.T0 = T0
        self.Tcf = Tcf
    
    def update(self, inlet=True, mv=0, dt=0, var=None): #, limits=None, loss=None, noise=None):
        if not self.noise: self.noise = 0 
        if not self.loss: self.loss = 0 

        if var:
            pvar = var[0]+random.normal()*var[1]
            
            self.qc = pvar * mv/10 * dt# vazao do liquido de resfriamento
            IC = [self.C0,self.T0,self.Tcf]             # initial condition
            
            self.pv = odeint(self.deriv,IC,[self.time,self.time+dt])              # perform simulation
            self.C0,self.T0,self.Tcf = self.pv[1]
            self.time += dt
        
        return self.pv
    
# pipe -----------------------------------------------------------
class pipe(object):
    """ 
    NOT USED - can be erased ?
    """ 
    def __init__(self):
        self.pv = 0.1
        self.limits = None
        self.noise = 0
        self.loss = 0

    def mix_pv(self,pv,dt):
        self.pv = (self.pv+pv*dt)/(1+dt)

    def __call__(self, inlet=True, mv=0, dt=0, var=None):
        return self.update(inlet, mv, dt, var)
    
    def __repr__(self):
        return (
            '{self.__class__.__name__}('
            'pv={self.pv!r}, limits={self.limits!r}, noise={self.noise!r}, '
            'loss={self.loss!r}'
            ')'
        ).format(self=self)
        
        
    def update(self, inlet=True, mv=0, dt=0, var=None): 
        
        if var:
            self.pv = var[0]
                
        return self.pv

# hydraulic -----------------------------------------------------------
class hydraulic(object):
    """ hydraulic and pneumatic on/off or controlled device
    """ 
    def __init__(self):
        self.pv = 0.1
        self.limits = None
        self.noise = 0
        self.loss = 0

    def mix_pv(self,pv,dt):
        self.pv = (self.pv+pv*dt)/(1+dt)

    def __call__(self, inlet=True, mv=0, dt=0, var=None):
        return self.update(inlet, mv, dt, var)
    
    def __repr__(self):
        return (
            '{self.__class__.__name__}('
            'pv={self.pv!r}, limits={self.limits!r}, noise={self.noise!r}, '
            'loss={self.loss!r}'
            ')'
        ).format(self=self)
        
    def update(self, inlet=True, mv=0, dt=0, var=None): #, limits=None, loss=None, noise=None):
        if not self.noise: self.noise = 0 
        if not self.loss: self.loss = 0 
        
        if var:
            pvar = var[0]+random.normal()*var[1]
            if mv>0:
                if inlet:
                    self.pv += pvar * mv/10 * dt
                else:
                    self.pv -= pvar * mv/10 * dt
                self.pv = noise(self.pv,self.noise) # TODO VERIFICAR!!!!
                
        #loss and limits
        self.pv -= self.loss * dt
        if self.limits is not None:
            if self.pv < min(self.limits): self.pv = min(self.limits)
            if self.pv > max(self.limits): self.pv = max(self.limits)

        return self.pv

# generic -----------------------------------------------------------
class generic(object):
    """ generic on/off or controlled device
    """ 
    def __init__(self):
        self.pv = 0.1
        self.limits = None
        self.noise = 0
        self.loss = 0

    def mix_pv(self,pv,dt):
        self.pv = (self.pv+pv*dt)/(1+dt)
        
    def __call__(self, inlet=True, mv=0, dt=0, var=None):
        return self.update(inlet, mv, dt, var)
    
    def __repr__(self):
        return (
            '{self.__class__.__name__}('
            'pv={self.pv!r}, limits={self.limits!r}, noise={self.noise!r}, '
            'loss={self.loss!r}'
            ')'
        ).format(self=self)
        
    def update(self, inlet=True, mv=0, dt=0, var=None): #, limits=None, loss=None, noise=None):
        if not self.noise: self.noise = 0 
        if not self.loss: self.loss = 0 
        
        if var:
            pvar = var[0]+random.normal()*var[1]
            if mv>0:
                if inlet:
                    self.pv += pvar * mv/10 * dt
                else:
                    self.pv -= pvar * mv/10 * dt
                self.pv = noise(self.pv,self.noise) # TODO VERIFICAR!!!!
                
        #loss and limits
        self.pv -= self.loss * dt
        if self.limits is not None:
            if self.pv < min(self.limits): self.pv = min(self.limits)
            if self.pv > max(self.limits): self.pv = max(self.limits)

        return self.pv

# flow -----------------------------------------------------------
class flow_meter(object):
    """ flow meter device to measure the inlet and outlet flow 
    TODO verify and improve
    """ 
    def __init__(self):
        self.pv = 0
        self.pvar_list = [0]
        self.limits = None
        self.noise = 0
        self.loss = 0

    def mix_pv(self,pv,dt):
        self.pv = (self.pv+pv*dt)/(1+dt)
        
    def __call__(self, inlet=True, mv=0, dt=0, var=None):
        return self.update(inlet, mv, dt, var)
    
    def __repr__(self):
        return (
            '{self.__class__.__name__}('
            'pv={self.pv!r}, limits={self.limits!r}, noise={self.noise!r}, '
            'loss={self.loss!r}'
            ')'
        ).format(self=self)
        
        
    def update(self, inlet=True, mv=0, dt=0, var=None):
        if not self.noise: self.noise = 0 
        if not self.loss: self.loss = 0 
        
        if var:
            pvar = random.normal(var[0],var[1])
            pvar = var[0]
            
            self.pvar_list.append(pvar)
            self.pv = 0
            if len(self.pvar_list)>(1/dt): # integrate 
                d=[ b-a for a,b in zip(self.pvar_list[::2],self.pvar_list[1::2]) ]
                self.pvar_list.pop(0)
                self.pv = sum(d)*10
                                    
        #loss and limits
        self.pv -= self.loss * dt
        if self.limits is not None:
            if self.pv < self.limits[0]: self.pv = self.limits[0]
            if self.pv > self.limits[1]: self.pv = self.limits[1]
                
        return self.pv
    


                        
if __name__ == '__main__':

    clear_screen()
    print('TEST')
