#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 19 09:29:29 2021

@author: glbramalho@gmail.com - Geraldo Ramalho
"""

import csv
# import warnings
from numpy.random import random as rnd
from numpy import exp
from colorama import Fore as fg, Back as bg, Style as st

# from datetime import datetime
from CTRL_PID import PID # used for the plant self.STRUCture
from PLANTsim_UTIL import *
from PLANTsim_MEMORY import Memory

################################### PLANT
##
###################################

class Plant:
    def __init__(self, plant={}):
        self.plant = plant
        self.state = None
        self.MV_MAX = 100
        self.ids = {}
        self.debug = []
        self.shutdown = False
        self.print_old_state = []
        self.KEYS = {'unt':['unity'],
                     'sec':['procvar','actuator','sensor'],  
                     'as':['actuator','sensor'], 
                     'prp':['type','pv','sp','mv','sys','bit','ctrl','noise',
                             'loss','active','enabled','flow','from_pv','sequence',
                             'to_pv','limits','label','inlet','if','word*'], 
                     'cst':['switch','relay','controller','memory','transmitter',
                              'mixer'],
                     'var':['aux','level','temperature','ph','oxigen','flow','conductivity','density','humidity','turbidity'],  
                }
        self.un={'level':'l','temperature':'`C','ph':'pH','flow':'l/s','oxigen':'%','humidity':'%','turbidity':'%'}

        self.STRUC = {'unity':{ 'enabled':(bool,),
                                'bit':(int,range(0,33)),
                                'sequence':(int,range(0,101)),
                                'label':(str,),
                                'procvar':{'type':(str,self.KEYS['var']),
                                            'pv':(int,range(0,1000)),
                                            'sp':(int,range(0,101)),
                                            'wordr_':(int,range(0,16)),
                                            'wordw_':(int,range(0,16)),
                                            'if':(str,),
                                            'sys':(str,),
                                            'limits':(tuple,),
                                            'noise':(float,),
                                            'loss':(float,),
                                            'bit':(bool,range(0,33)),
                                            'sequence':(bool,range(0,101)),
                                            'label':(str,),
                                            },
                                'actuator':{'type':(str,self.KEYS['cst']),
                                            'active':(bool,),
                                            'bit':(int,range(0,33)),
                                            'ctrl':(str,),
                                            'ctrl_par':(tuple,),
                                            'ctrl_pv':(str,),
                                            'from_pv':(str,),
                                            'to_pv':(str,),
                                            'mv':(str,range(0,101)),
                                            'wordw_':(int,range(0,16)),
                                            'flow':(float,),
                                            'inlet':(bool,),
                                            'label':(str,),
                                            },
                                'sensor':{'type':(str,self.KEYS['cst']),
                                        'active':(bool,),
                                        'bit':(int,range(0,33)),
                                        'from_pv':(str,),
                                        'label':(str,),
                                        }
                    }
                }        

    def var(self,*type_var):
        """ returns a list of valid key variables
        """
        if isinstance(type_var,str): type_var = [ type_var]
        ret = []
        for tv in type_var:
            for x in self.KEYS['var']:
                ret.append(x+'_'+tv)
        return ret
        
    # returns the type of a key
    def key_type(self,key):
        """ returns the type of a key
        """
        for t in self.KEYS:
            if any([x in key or key in x for x in self.KEYS[t]]):        
                break
        return t
    
    def contains_a_key_type(self,key_type,elements):
        """ verify if an element contains a key
        """
        return any([x in elements for x in self.KEYS[key_type]])  
                
    def debug_add(self, *args):
        self.debug.append(args)

    def words_addr(self,uu,rr,dd):
        """ handling wordr_pv and wordw_sp -  used in MEMORY class
        """
        ret = []
        addr = [ x if 'word' in x else None for x in self.r(uu,rr,dd)]
        if any(addr):
            for xx in addr:
                if not xx is None:
                    t,nm = xx.split('_')
                    ret.append([xx,t[-1] in 'wW',nm])
        return ret

    # handling from_pv / from_unity
    def id_expand(self,var,id_unity=None):
        id_pv = var
        if var is not None:
            if '.' in var:
                id_unity,id_pv = var.split('.')
            # else:
                # raise Exception ('*** ID_EXPAND: invalid id!')
        return id_unity,id_pv

    # read/write data from/to plant structure
    def rw(self,sentence,write_value=None):
        """ This functions sets values or returns multiples data formats (value,list, dict)
        uu = unity id
        rr = section
        dd = procvar
        pp = property
        
        input:      output:
        uu.rr.dd.pp property value
        uu.dd.pp    property value
        uu.pp       list of values of property 'pp'; except for uu = 'unity'
        uu          dict
        uu.rr       dict of unity 'uu' and section 'rr'
        rr          dict of section 'rr' for all unities
        rr.dd       list of property values for section 'rr' for all unities
        """
        names = sentence.split('.')
        # print('+++',names)
        uu,rr,dd,pp,value = [None]*5
        val_list = []
        debug = 0
        if names: #1
            uu = names.pop(0)            
            if not names and uu in self.KEYS['sec']:
                rr = uu
                val_list={}
                for uu in self.plant:
                    if self.plant[uu].get(rr):
                        value = self.plant[uu][rr]
                        # print('+++',uu,rr,value)
                        if not val_list.get(uu):
                            val_list[uu]={}
                        if not val_list[uu].get(rr):
                            val_list[uu][rr]={}
                        # print('+++ val_list',val_list)
                        val_list[uu][rr] = value
                return val_list                
            elif names and uu in self.KEYS['sec']:
                rr = uu
                pp = names.pop(0)
                for uu in self.plant:
                    if self.plant[uu].get(rr):
                        for dd in self.plant[uu][rr]:
                            value = self.plant[uu][rr][dd].get(pp)
                            # print('+++3',uu,rr,dd,'names',names,'value',value)
                            if value is not None:
                                val_list.append(value)
                return val_list
                        
            value = self.plant.get(uu)            
            if names: #2
                rr = names.pop(0)
                if rr in self.KEYS['prp']: 
                    pp = rr
                    dd = uu
                    for rr in self.KEYS['unt']:
                        value = self.plant[uu][rr][uu].get(pp)
                        if value is not None: break
                    if value is None:
                        for rr in self.KEYS['sec']:
                            if self.plant[uu].get(rr):
                                for dd in self.plant[uu][rr]:
                                    value = self.plant[uu][rr][dd].get(pp)
                                    if value is not None:
                                        val_list.append(value)
                elif rr in self.KEYS['unt']:
                    value = self.plant[uu].get(rr)
                    dd = uu
                    if names and names[0] == dd:
                        names.pop(0)
                    # print('+++2',uu,rr,dd,'names',names,'value',value)
                elif rr in self.KEYS['sec']:
                    value = self.plant[uu].get(rr)                
                else:
                    dd = rr
                    # print('+++2',uu,rr,dd,'names',names)
                    for rr in self.KEYS['sec']:
                        tmp = self.plant[uu].get(rr)
                        if tmp is not None: 
                            value = self.plant[uu][rr].get(dd)   
                            if value is not None: break
                if names: #3
                    if dd is None: 
                        dd = names.pop(0)
                        value = self.plant[uu][rr].get(dd)
                        if not names and rr in self.KEYS['sec'] and dd in self.KEYS['prp']:
                            pp = dd
                            # print('+++3',uu,rr,dd,'names',names,'value',value)
                            for dd in self.plant[uu][rr]:
                                value = self.plant[uu][rr][dd].get(pp)
                                if value is not None:
                                    val_list.append(value)
                    if names: #4
                        pp = names.pop(0)
                        if pp == dd and names:
                            pp = names.pop(0)
                        # print('+++4',uu,rr,dd,pp,'names',names,'value',value) 
                        if self.plant[uu].get(rr):
                            if self.plant[uu][rr].get(dd):
                                value = self.plant[uu][rr][dd].get(pp)
        if val_list: 
            return val_list
        if write_value is None:
            return value
        else:
            self.plant[uu][rr][dd][pp] = write_value
                

    def r(self,*sentence):
        """ provides easy access to read the plant structure data
            widely used in this class and by others
        """
        if len(sentence)>0:
            if len(sentence)==1:
                if isinstance(sentence[0],list): sentence = '.'.join(sentence[0])
                else:
                    sentence = str(sentence[0])
            else:
                if sentence[0] in sentence[1]: sentence = sentence[1:] # eliminates unity if already exisits in the id

                sentence = '.'.join(sentence)

            return self.rw(sentence.replace(' ','.'), write_value=None)
        else:
            return self.plant

    def w(self,*sentence):
        """ provides easy access to write the plant structure data
            widely used in this class and by others
        """
        value = None
        if len(sentence)==2:
            value = sentence[1]
            sentence = str(sentence[0])
        else:
            if sentence[0] in sentence[1]: sentence = sentence[1:] # eliminates unity if already exisits in the id
            value = sentence[-1]
            sentence = '.'.join(sentence[:-1])
        return self.rw(sentence.replace(' ','.'),write_value=value)

    # update parameters from file
    def update_params(self):
       # adjust  SYS and CTRL parameters
        """ updates the data in the plant structure
        """
        for uu in self.r():
            for rr in self.r(uu):
                for dd in self.r(uu,rr):
                    if self.r(uu,rr,dd) is not None:

                        if self.r(uu,rr,dd,'sys'):
                            self.r(uu,rr,dd,'sys').pv = self.r(uu,rr,dd,'pv')
                            self.r(uu,rr,dd,'sys').limits = self.r(uu,rr,dd,'limits')
                            self.r(uu,rr,dd,'sys').noise = self.r(uu,rr,dd,'noise')
                            self.r(uu,rr,dd,'sys').loss = self.r(uu,rr,dd,'loss')
                        if  self.r(uu,rr,dd,'ctrl'):
                            ctrl_unity_id,ctrl_pv_id = self.id_expand( self.r(uu,dd,'ctrl_pv'),id_unity=uu ) # ALTERADO from -> to
                            unity_id,pv_id = self.id_expand( self.r(uu,dd,'to_pv'),id_unity=uu ) # ALTERADO from -> to
                            if pv_id is None:
                                unity_id,pv_id = self.id_expand( self.r(uu,dd,'from_pv'),id_unity=uu ) # ALTERADO from -> to
                            if ctrl_pv_id is None:
                                ctrl_unity_id,ctrl_pv_id = unity_id,pv_id

                            setpoint = self.r(ctrl_unity_id,'procvar',ctrl_pv_id,'sp')
                            if not setpoint: setpoint = 0
                            self.r(uu,rr,dd,'ctrl').setpoint = setpoint

                            self.r(uu,rr,dd,'ctrl').output_limits = (0,self.MV_MAX)
                            self.r(uu,rr,dd,'ctrl').sample_time = 0.01
                            self.r(uu,rr,dd,'ctrl').tunings = self.r(uu,rr,dd,'ctrl_par') if self.r(uu,rr,dd,'ctrl_par') else [0,0,0]
                            inlet = self.r(uu,rr,dd,'inlet')
                            if inlet is not None and not inlet:
                                self.r(uu,rr,dd,'ctrl').set_error(lambda e: -e)


    # print plant definition file
    def print_file(self,file_name):
        """ show the plant definition file in colors
        """
        ids = {}
        # load plant self.STRUCture
        with open(file_name,'r') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=' ')
            uu = ''
            rr = ''
            dd = ''
            spc = ' '*8
            for row in csv_reader:
                while '' in row: row.remove('')
                if not row: 
                    print('')
                    continue
                if '#' in row[0]: 
                    print(fg.WHITE,' '.join(row))
                    continue
                spc,n,c = ' '*8,0,fg.BLUE+st.BRIGHT
                if self.contains_a_key_type('unt',row):    
                    spc,n,c = '',1,fg.BLUE+st.BRIGHT
                if self.contains_a_key_type('sec',row): 
                    spc = ' '*4
                print(spc, end='')
                for i,r in enumerate(row):
                    if len(row)>10 and i in [9,17]:
                        print('')
                        print(spc,' '*len(row[0]), end='')
                    color = fg.RESET
                    if i == n:
                        color = c
                        ids[r] = uu
                    if r in self.KEYS['unt'] or r in self.KEYS['sec']: 
                        color = fg.YELLOW+st.BRIGHT
                        uu = r
                        r = r.upper()
                    if r in ids or '.' in r or '>' in r or '<' in r or '<=' in r or '>=' in r or '==' in r:
                        color = c
                    if r in ['false','true']: 
                        r = r.capitalize()
                    try:
                        if isinstance(eval(r),(int,float,tuple,list)) or callable(eval(r)):
                            color = fg.GREEN+st.BRIGHT
                    except:
                        pass
                    if r in self.KEYS['prp'] or 'word' in r or 'ctrl' in r: 
                        color = fg.CYAN
                        prop = r
                    # if r in self.KEYS['cst']: 
                    if self.contains_a_key_type('cst',r) or self.contains_a_key_type('var',r):
                        color = fg.GREEN
                        if len(self.STRUC['unity'][uu][prop])>1: 
                            valok = r in self.STRUC['unity'][uu][prop][1]
                        else:
                            valok = True
                        if not valok: color = fg.RED+st.BRIGHT 
                    print(color, r, st.RESET_ALL, sep='', end=' ')
                print(st.RESET_ALL)
                

    # load plant definition from file
    def load(self,file_name):
        """ read the plant definition file
            completes missing properties
            creates ids structure - used to eval expressions
            fixes incomplete ids (unity.id)
        """
        # load plant self.STRUCture
        with open(file_name,'r') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=' ')
            self.plant = {}
            uu = ''
            rr = ''
            dd = ''
            for row in csv_reader:
                while '' in row: row.remove('') # remove empty elements
                if '#' in row: row = row[:row.index('#')] # remove comments
                if not row: continue
                #
                if row[0] in self.STRUC: # 1st. level: unity
                    uu = row[1] # unity id
                    rr = ''
                    dd = ''
                    self.plant[uu] = {}
                    # this is to ensure provisory compatibility with the old structure
                    rr = 'procvar'
                    if self.plant[uu].get('procvar') is None:
                        self.plant[uu]['procvar'] = {}#{'unity':{}}
                        self.plant[uu]['unity'] = {uu:{}}# {'name':uu}
                    #
                    for nm,val in zip(row[2::2],row[3::2]):
                        val = val.replace('false','False')
                        val = val.replace('true','True')
                        valok = True
                        try:
                            val = eval(val)
                        except:
                            pass
                        # print('+++',nm,self.STRUC['unity'][nm])
                        ok = isinstance(val, (self.STRUC['unity'][nm][0], str) ) 
                        if len(self.STRUC['unity'][nm])>1: 
                            valok = val in self.STRUC['unity'][nm][1]
                            valid = self.STRUC['unity'][nm]
                        
                        if (nm in self.STRUC['unity']) or ( 'word' in nm  and nm[:6] in self.STRUC['unity'] ):
                            # do not remove: 
                            self.plant[uu]['unity'][uu][nm] = val
                            # self.plant[uu]['procvar']['unity'][nm] = val
                        #
                        if not valok: 
                            raise Exception('*** LOAD: value is invalid!',uu,dd,nm,val,' valid =',valid)
                else:
                    if row[0] in self.STRUC['unity']: # 2st. level: procvar,actuator,sensor
                        rr = row[0]
                        dd = ''
                        if self.plant[uu].get(rr) is None:
                            self.plant[uu][rr] = {}
                    else: # 3st. level: variables
                        dd = row[0]
                        if self.plant[uu][rr].get(dd) is None:
                            self.plant[uu][rr][dd] = {}
                    for nm,val in zip(row[1::2],row[2::2]):
                        val = val.replace('false','False')
                        val = val.replace('true','True')
                        valok = True
                        try:
                            val = eval(val)
                        except:
                            pass
                        ok = False
                        if nm in self.STRUC['unity'][rr]:
                            ok = isinstance(val, self.STRUC['unity'][rr][nm][0] ) or callable(val)
                            if len(self.STRUC['unity'][rr][nm])>1: 
                                valok = val in self.STRUC['unity'][rr][nm][1] or val in self.var('calc','var')
                                valid = self.STRUC['unity'][rr][nm]
                        if not ok and nm[:6] in self.STRUC['unity'][rr]:
                            ok = isinstance(val, self.STRUC['unity'][rr][nm[:6]][0] ) or callable(val)
                            if len(self.STRUC['unity'][rr][nm[:6]])>1: 
                                valok = val in self.STRUC['unity'][rr][nm[:6]][1] or val in self.var('calc','var')
                                valid = self.STRUC['unity'][rr][nm[:6]]
                        if dd:
                            if (nm in self.STRUC['unity'][rr]) or ( 'word' in nm  and nm[:6] in self.STRUC['unity'][rr] ):
                                self.plant[uu][rr][dd][nm] = val
                        if not valok: 
                            raise Exception ('*** LOAD: value is invalid!',uu,dd,nm,val,' valid =',valid)


        # complete missing properties and makes adjustments
        ids = {}
        for uu in self.plant:
            ids[uu] = []
            for rr in self.plant[uu]:
                if rr not in self.KEYS['sec']: continue
                for dd in self.plant[uu][rr]:
                    # print('+++ ',uu,rr,dd)                    
                    if self.r(uu,rr,dd,'label') is None: self.plant[uu][rr][dd]['label']=dd
                    if rr in ['unity']:
                        # if self.r(uu,rr,'enabled') is None: self.plant[uu][rr]['enabled']=False
                        if self.r(uu,rr,dd,'enabled') is None: self.plant[uu][rr][dd]['enabled']=False
                        if self.r(uu,rr,dd,'sequence') is None: self.plant[uu][rr][dd]['sequence']=0
                    if rr in ['procvar']:
                    # if rr in ['procvar'] and dd not in ['unity']:
                        ids[uu].append(dd)
                        if self.r(uu,rr,dd,'type') is None: self.plant[uu][rr][dd]['type']='level_var'
                        if self.r(uu,rr,dd,'type') in self.var('calc'):
                            if self.r(uu,rr,dd,'sys') is None: self.plant[uu][rr][dd]['sys']=flow_meter()
                            if self.r(uu,rr,dd,'pv') is None: self.plant[uu][rr][dd]['pv']=0
                            if self.r(uu,rr,dd,'sp') is None: self.plant[uu][rr][dd]['sp']=0
                            if self.r(uu,rr,dd,'limits') is None: self.plant[uu][rr][dd]['limits']=[0,15]
                            if self.r(uu,rr,dd,'noise') is None: self.plant[uu][rr][dd]['noise']=0.0
                            if self.r(uu,rr,dd,'loss') is None: self.plant[uu][rr][dd]['loss']=0.0
                        if self.r(uu,rr,dd,'type') in self.var('var'):
                            if self.r(uu,rr,dd,'sys') is None: self.plant[uu][rr][dd]['sys']=generic()
                            if self.r(uu,rr,dd,'pv') is None: self.plant[uu][rr][dd]['pv']=0
                            if self.r(uu,rr,dd,'limits') is None: self.plant[uu][rr][dd]['limits']=[0,100]
                            if self.r(uu,rr,dd,'sp') is None: self.plant[uu][rr][dd]['sp']=max(self.plant[uu][rr][dd]['limits'])
                            if self.r(uu,rr,dd,'noise') is None: self.plant[uu][rr][dd]['noise']=0.0
                            if self.r(uu,rr,dd,'loss') is None: self.plant[uu][rr][dd]['loss']=0.0
                            if self.r(uu,rr,dd,'if') is None:
                                self.plant[uu][rr][dd]['if']=None
                            else:
                                self.plant[uu][rr][dd]['limits']=[0,1]
                                self.plant[uu][rr][dd]['noise']=0.0
                                self.plant[uu][rr][dd]['loss']=0.0
                                self.plant[uu][rr][dd]['pv']=0
                                self.plant[uu][rr][dd]['sp']=max(self.plant[uu][rr][dd]['limits'])
                                self.plant[uu][rr][dd]['sys']=generic()

                    if rr in ['actuator','sensor']:
                        ids[uu].append(dd)
                        if self.r(uu,rr,dd,'active') is None: self.plant[uu][rr][dd]['active']=False
                        if rr in ['actuator']:
                            if self.r(uu,rr,dd,'type') is None: self.plant[uu][rr][dd]['type']='relay'
                            if self.r(uu,rr,dd,'type') not in ['memory']:
                                if self.r(uu,rr,dd,'flow') is None: self.plant[uu][rr][dd]['flow']=0.1
                            if self.r(uu,rr,dd,'type') in ['controller']:
                                if self.r(uu,rr,dd,'mv') is None: self.plant[uu][rr][dd]['mv']=0
                                if self.r(uu,rr,dd,'ctrl') is None: self.plant[uu][rr][dd]['ctrl']=PID()
                                # ctrl_par=None means PID is disabled and mv defines the aperture => if self.r(uu,rr,dd,'ctrl_par') is None: self.plant[uu][rr][dd]['ctrl_par']=[0.5,0.0,0.0]
                        if rr in ['sensor']:
                            if self.r(uu,rr,dd,'type') is None: self.plant[uu][rr][dd]['type']='switch'

                        if self.r(uu,rr,dd,'type') in ['controller','relay','transmitter']:
                            from_unity_id,from_pv_id = self.id_expand( self.r(uu,rr,dd,'from_pv'), id_unity=uu)
                            to_unity_id,to_pv_id = self.id_expand( self.r(uu,rr,dd,'to_pv'), id_unity=uu)
                            if to_pv_id is None:
                                to_unity_id,to_pv_id = from_unity_id,from_pv_id
                            from_pv = from_unity_id+'.'+from_pv_id
                            to_pv = to_unity_id+'.'+to_pv_id
                        if self.r(uu,rr,dd,'type') in ['controller','relay','transmitter']:
                            self.plant[uu][rr][dd]['from_pv'] = from_pv
                            self.plant[uu][rr][dd]['to_pv'] = to_pv
                        if self.r(uu,rr,dd,'type') in ['switch']:
                            self.plant[uu][rr][dd]['from_pv'] = from_pv
                        nominal_flow = self.r(uu,rr,dd,'flow')
                        if self.r(uu,rr,dd,'type') in ['controller','relay']:
                            ctrl_pv = self.r(uu,rr,dd,'ctrl_pv')
                            actuator_id = self.r(to_unity_id,to_pv_id,'if')
                            if actuator_id:
                                if ctrl_pv is None:
                                    ctrl_pv =  self.r(to_unity_id,actuator_id,'to_pv')
                                nominal_flow =  self.r(to_unity_id,actuator_id,'flow')
                            if ctrl_pv is None:
                                ctrl_pv = to_pv
                        if self.r(uu,rr,dd,'type') in ['controller']:
                            self.plant[uu][rr][dd]['ctrl_pv'] = ctrl_pv
                        flow = self.r(uu,rr,dd,'flow')
                        if flow is not None:
                            if flow>nominal_flow: self.plant[uu][rr][dd]['flow'] = nominal_flow


        # complete all ids (unity.id)
        for uu in self.plant:
            for rr in self.plant[uu]:
                # if rr not in self.KEYS['sec']: continue
                for dd in self.plant[uu][rr]:
                    for pp in self.plant[uu][rr][dd]:
                        value = self.plant[uu][rr][dd][pp]
                        if pp in ['enabled','active','ctrl_pv','from_pv','to_pv','if'] :
                            for i in ids[uu]:
                                if isinstance(value,str):
                                    if '.'+i not in value and i in value:
                                        new_id = '.'.join([uu,i])
                                        self.plant[uu][rr][dd][pp] = value.replace(i, new_id)

        self.update_params()
        
        self.update_ids()

        # verify structure
        self.verify()

        
    def verify(self):        
        """ verify plant structure 
        TODO verify and finish the code
        """
        
        # check for inconsistency that may cause odd behavior or exceptions
        warning = []
        pv_id = {}
        for uu in self.plant:
            pv_id[uu]=[]
            for rr in self.plant[uu]:
                for dd in self.plant[uu][rr]:
                    if rr in ['procvar']:
                        if self.r(uu,rr,dd,'sys') is not None:
                            pv_id[uu].append(dd)
                        # prop_type = 'sys'
                        # if self.r(uu,rr,dd,prop_type) is None: prop_type = 'unity'

                    if rr in ['actuator','sensor']:
                        from_unity,vv = self.id_expand( self.r(uu,rr,dd,'from_pv'), id_unity=uu)
                        if vv is None:
                            if self.r(uu,rr,dd,'ctrl') is not None:
                                warning.append([uu,rr,dd,'does not contains a pv id ',None,None])
                        else:
                            if from_unity is not None:
                                if self.r(from_unity) is not None:
                                    if self.r(from_unity,'procvar',vv) is None:
                                        warning.append([uu,rr,dd,'does not contains a valid pv id:',vv,'from',from_unity])
                        prop_type = 'ctrl'
                        if self.r(uu,rr,dd,prop_type) is None: prop_type = 'onoff'

                    # # verify
                    # for pr in DEFAULT[rr][prop_type]:
                    #     if self.r(uu,rr,dd,pr) is None:
                    #         value = DEFAULT[rr][prop_type][pr]
                    #         if value is not None:
                    #             warning.append([uu,rr,dd,'does not contains a "{}" definition. Assuming external control.'.format(pr),None,None])
                    #             # self.w(uu,rr,dd,pr, value)

        # show inconsistency
        if warning:
            # warnings.warn('PLANT.LOAD warnings:')

            print('PLANT.load warnings:')
            for w in warning:
                uu = [x for x in w if x is not None]
                print('  -',' '.join(uu))
                if w[-1] is not None:
                    print('    valid',w[-1],'pv ids are:',', '.join(pv_id[w[-1]]))
                elif w[-2] is not None:
                    print('    valid pv ids are:',', '.join(pv_id[w[0]]))
                    
        invalid_ids = []
        for rr in self.KEYS['sec'][1:]:
            for pp in self.STRUC['unity']['actuator']:
                if 'pv' in pp:
                    ids = self.r(rr,pp)
                    if ids:
                        error = [ x for x in ids if x not in self.ids]
                        if error:
                            invalid_ids.append([rr,pp,error])
        if invalid_ids:
            # warnings.warn('PLANT.LOAD warnings:')
            print('PLANT.load error:')
            print('Section','\t','Property','\t','Value')
            for s,p,v in invalid_ids:
                print(s,'\t',p,'\t',v)
            raise Exception('*** PLANT.load error!')
                            
                        

    def unity(self):
        return self.ids['unity']
    
    def prop(self):
        return self.ids['procvar']
    
    def actuator(self):
        return self.ids['actuator']
    
    def sensor(self):
        return self.ids['sensor']

    def update_ids(self):
        """ update ids structure with the plant values
        """
        self.state = []
        self.ids = {}
        for uu in self.r():
            # uu_enabled = self.r(uu,'unity',uu,'enabled')
            for rr in self.r(uu):
                # if rr not in self.KEYS['sec']: continue
                for dd in self.r(uu,rr):
                    value = self.r(uu,rr,dd,'enabled')
                    # value = uu_enabled
                    if value is None:
                        value = self.r(uu,rr,dd,'active')
                        if value is None:
                            value = self.r(uu,rr,dd,'pv')
                    # args
                    args = self.r(uu,rr,dd)
                    # print('+++',uu,rr,dd)
                    for a in args:
                        self.ids[uu+'.'+dd+'.'+a] = args[a]
                        if a in ['pv','active','enabled']:
                            if uu == dd:
                                self.ids[uu] = args[a]
                            else:
                                self.ids[uu+'.'+dd] = args[a]
                        if a in ['limits']:
                            self.ids[uu+'.'+dd+'.range'] = diff(args[a])


    def eval_exp(self,expression,value=None):
        """ evaluate expressions as the 'eval' python function
            using unity.id as variable names
        """
        exp = expression
        if value is None:
            if exp is None or not isinstance(exp,str):
                return exp
            if exp in self.ids:
                try:
                    return eval(self.ids.get(exp))
                except:
                    return self.ids.get(exp)
            for i in sorted(self.ids, key=len, reverse=True):
                if i in exp:
                    value = self.ids.get(i)
                    if isinstance(value,dict):
                        return value
                    exp = exp.replace(i,str(value))
            try:
                return eval(exp)
            except:
                return exp
                self.debug_add('expression contains an invalid id:',expression)
                self.is_run = False
        else:
            if exp in self.ids:
                self.ids[exp] = value
                return value
            else:
                self.debug_add('attribution error:',expression)
                self.is_run = False


    def is_active(self,value):
        """ used to return the state of a unity, actuator or sensor
        """        
        val = value
        n = 5
        while not isinstance(val,bool) and n>0 and val is not None:
            val = self.eval_exp(value)
            value = val
            n -=1
        if isinstance(val,dict):
            val = list(val.values())[0]
        return val

    # show table of PLANT memory
    def show_mem_state(self):
        """ shows the plant memory formated in columns
        """
        bitS = [[]]*32
        bitA = [[]]*32
        word = [[]]*32
        NWS,NWA=16,16 # TODO must read from .ini

        state_tmp = {}        
        for uu in self.plant:
            for rr in self.plant[uu]:
                if rr not in self.KEYS['sec']: continue
                for dd in self.plant[uu][rr]:
                    for zz in self.plant[uu][rr][dd]:
                        value = self.plant[uu][rr][dd].get(zz)
                        if value is not None:
                            label = self.plant[uu][rr][dd].get('label')
                            label = ''
                            if label is None: label = ''
                            if zz in 'bit':
                                logic = self.is_active( self.plant[uu][rr][dd].get('active') )
                                nm = 'active'
                                if logic is None:
                                    logic = self.is_active( self.plant[uu][rr][dd].get('enabled') )
                                    # logic = self.is_active( self.plant[uu]['unity'][uu].get('enabled') )
                                    nm = 'enabled'
                                state_tmp['.'.join([uu,rr,dd,nm])] = logic

                                bstr = [' ','*'][logic]
                                bright=st.BRIGHT if logic else ''
                                if rr in ['sensor','procvar']:
                                    from_unity,from_pv = self.id_expand(self.plant[uu][rr][dd].get('from_pv'), id_unity=uu)

                                    val = ''
                                    if from_pv in self.plant[from_unity]['procvar']:
                                        val = self.plant[uu][rr][dd].get(nm)
                                        if val is None:
                                            val = ''
                                        else:
                                            # print('+++ ->',uu,rr,dd,nm,'val=',val)
                                            if uu+'.' in val: val = val.replace(uu+'.','')
                                            val = ' '+val

                                    if not bitS[value]:
                                        bitS[value] = [fg.MAGENTA+st.BRIGHT,bstr,st.RESET_ALL,'.'.join([uu,dd]),label,fg.CYAN+bright,val,st.RESET_ALL]
                                    else:
                                        for x in [',','.'.join([uu,dd]),label,fg.CYAN+bright,val,st.RESET_ALL]:
                                            bitS[value].append(x)
                                if rr in 'actuator':
                                    mv = self.plant[uu][rr][dd].get('mv')
                                    if mv is None:
                                        mv=''
                                    else:
                                        mv = ' %d'%(mv/self.MV_MAX*100)+'%'
                                    if not bitA[value]:
                                        bitA[value] = [fg.MAGENTA+st.BRIGHT,bstr,st.RESET_ALL,'.'.join([uu,dd]),label,fg.GREEN+bright,mv,st.RESET_ALL]
                                    else:
                                        for x in [',','.'.join([uu,dd]),label,fg.GREEN+bright,mv,st.RESET_ALL]:
                                            bitA[value].append(x)

                                    # pv controller
                                    unity_id,pv_id = self.id_expand( self.r(uu,rr,dd,'ctrl_pv'), id_unity=uu)
                                    if pv_id is None:
                                        unity_id,pv_id = self.id_expand( self.r(uu,rr,dd,'to_pv'), id_unity=uu)
                                    if pv_id and pv_id not in bitA[value]: # show only if is differente from previous
                                        bitA[value].append(fg.CYAN)
                                        bitA[value].append('->')
                                        if unity_id == uu:
                                            bitA[value].append(pv_id)
                                        else:
                                            bitA[value].append(unity_id+'.'+pv_id)
                                        bitA[value].append(st.RESET_ALL)
                            if 'word' in zz:
                                value = self.plant[uu][rr][dd][zz]
                                r,nm = zz.split('_')
                                n = self.plant[uu][rr][dd].get(nm)

                                state_tmp['.'.join([uu,rr,dd,nm])] = n

                                if self.state:
                                    bright = st.BRIGHT if state_tmp['.'.join([uu,rr,dd,nm])]!=self.state['.'.join([uu,rr,dd,nm])] else ''

                                limits = self.plant[uu][rr][dd].get('limits')
                                if_actuator = self.plant[uu][rr][dd].get('if')
                                if if_actuator is None: if_actuator=''
                                else: if_actuator = '?'+if_actuator
                                if limits is None: limits = [0,self.MV_MAX]
                                nrange = diff(limits)
                                numbars = 10
                                nbar = int((n)/(nrange)*numbars)
                                barstr = 'o'*nbar+'.'*(numbars-nbar)
                                vstr1 = '%4d '%(n)
                                vstr2 = ('%-'+str(numbars)+'s')%(barstr)
                                no = vstr2.find('.')
                                if no<0: no=len(vstr2)
                                vstr2 = bg.CYAN+fg.CYAN+vstr2[:no]+st.RESET_ALL+fg.WHITE+vstr2[no:]
                                vstr3 = fg.CYAN+st.NORMAL+'%3d '%(nrange)
                                if r[-1] in 'wW':
                                    value += NWS
                                if not word[value]:
                                    word[value] = [fg.CYAN+bright,vstr1,fg.WHITE+st.NORMAL,vstr2,fg.BLUE+st.BRIGHT,vstr3,st.RESET_ALL,'.'.join([uu,dd,nm]),fg.CYAN,if_actuator,st.RESET_ALL,label]
                                else:
                                    for x in [',','.'.join([uu,dd,nm]),fg.CYAN,if_actuator,st.RESET_ALL,label]:
                                        word[value].append(x)
        self.state  = state_tmp

        # print_row prints with color preserving spacing
        def print_row(line=None):
            spc = 0
            if not line:
                print(st.RESET_ALL)
                return 0
            spc = 0
            for s in line:
                if fg.WHITE[0] not in s:
                    spc += len(s)
                print(s,end='')
            return spc

        Nspc=[25,40,45]
        # print_row()
        print_row(fg.RESET+'_'*(sum(Nspc)))
        print_row()
        spc=print_row([fg.RESET,'___',fg.BLACK+bg.WHITE,' Sensor (r/o) ',st.RESET_ALL])
        spc=print_row([fg.RESET,'_'*(Nspc[0]-spc)])
        spc=print_row([fg.RESET,'___',fg.BLACK+bg.CYAN,' Actuator (r/w) ',st.RESET_ALL])
        spc=print_row([fg.RESET,'_'*(Nspc[1]-spc)])
        spc=print_row([fg.RESET,'___',fg.BLUE+bg.WHITE+st.DIM,' Word (0-15 r/o; 16-31 r/w)   ',st.RESET_ALL])
        spc=print_row([fg.RESET,'_'*(Nspc[2]-spc)])

        print_row()
        print_row()
        niw,nb,nw = 0,0,0
        wc=fg.WHITE
        while nb<32:
            spc=print_row([fg.WHITE,'%2d'%(nb%16)]+bitS[nb])
            spc=print_row([' '*(Nspc[0]-spc)])
            spc=print_row([fg.CYAN,'%2d'%(nb%16),st.RESET_ALL]+bitA[nb])
            if nw<(NWS+NWA):
                spc=print_row([' '*(Nspc[1]-spc)])
                spc=print_row([wc,'%2d'%(niw),st.RESET_ALL]+word[nw])
            else:
                print_row([' '])
            print_row()
            nb+=1
            nw+=1
            niw+=1
            if niw>=(NWS):
                niw=0
                wc = fg.CYAN
        print_row(fg.RESET+'_'*(sum(Nspc)))
        print_row()

    def print_process_sequence(self):
        """ show the plant sequenc defined by from_pv/to_pv on the actuators
        """
        act = {}
        tmp = {}
        for uu in self.r():
            for rr in self.r(uu):
                for dd in self.r(uu,rr):
                    if self.r(uu,rr,dd,'type') in ['controller','relay']:
                        from_unity,from_pv = self.id_expand(self.r(uu,rr,dd,'from_pv'))
                        to_unity,to_pv = self.id_expand(self.r(uu,rr,dd,'to_pv'))
                        if_actuator,is_active,ctrl_unity,ctrl_pv = self.linked_actuator(to_unity,to_pv)
                        pv_type = self.r(from_unity,from_pv,'type')
                        if 'level' in pv_type:
                            tmp[from_unity] = ctrl_unity
                            act[from_unity] = [self.r(uu,rr,dd,'active'), uu,to_unity]
        # for t in tmp: print('+++',t,tmp[t])
        unity = []
        for i,x in enumerate(tmp.keys()):
            sequence = self.r(x,'unity','sequence')
            if sequence == 0: break
        x = list(tmp.keys())[i]
        print(bg.WHITE+fg.BLACK,' '*16,end='')
        while x:
            unity.append(x)
            x = tmp.get(x)
            if (x in unity):
                break
        for i,x in enumerate(unity):
            if self.r(x+'.lvl.pv'):
                print(fg.BLACK+st.BRIGHT+x,sep=' ',end='')
            else:
                print(fg.BLACK+st.DIM+x,sep=' ',end='')
            if i<len(unity)-1:
                if act.get(x):
                    print(fg.BLACK+st.DIM,'  | ',sep='',end='')
                else:
                    print(fg.BLACK+st.DIM,'  | ',sep='',end='')
        print('   ', st.RESET_ALL) 
        #
        if not self.print_old_state: self.print_old_state = {}
        for ty in self.KEYS['var']:
            line = []
            for x in unity:
                if self.print_old_state.get(x) is None: 
                    self.print_old_state[x] = {}
                found = False
                for pv in self.r(x+'.procvar'):  
                    if pv not in self.KEYS['unt'] and ty in self.r(x,pv,'type'): 
                        found = True
                        break
                if not found:
                        line = line + ['',' '*7]
                else:
                    if self.print_old_state[x].get(ty) is None: 
                        self.print_old_state[x][ty] = ''
                    val = self.r(x+'.'+pv+'.pv')
                    if val is not None:
                        strval = '%3d%-3s '%(val,self.un.get(ty))
                    else:
                        strval = ' '*7
                    bright = fg.WHITE
                    if self.print_old_state[x][ty] != strval: bright = fg.RESET
                    self.print_old_state[x][ty] = strval
                    if self.un.get(ty) is not None:
                        line = line + [bright,strval]
            if any([len(x.strip())>0 for x in line]):
                line = [fg.WHITE+'%15s: '%(ty,)] + line
                for l in line:
                    print(l,sep='',end='')
                print('')

    def print_unity(self, unity=['*'], spc_=25, only_enabled=False, only_active=False):
        """ show a unity of the plant structure
        """
        if isinstance(unity,str): unity = [unity]
        strON = '*'
        for uu in unity:
            uu_enabled = self.is_active(self.r(uu,'unity',uu,'enabled'))
            label = self.r(uu,'unity',uu,'label')
            if label is None: label = uu
            print(fg.GREEN+st.BRIGHT+uu+st.RESET_ALL,label.upper().replace('_',' '),'-'*(100-len(label)))
            if not self.r(uu) or (only_enabled and not uu_enabled): continue
            for rr in self.r(uu):
                if rr not in self.KEYS['sec']: continue
                header = []
                data = []
                footer = []
                for dd in self.r(uu,rr):
                    unity_id_from,unity_pv_from = '',''
                    unity_id_to,unity_pv_to = '',''
                    uid_from,uid_to = '',''
                    value = self.r(uu,rr,dd,'enabled')
                    value2=''
                    if value is None:
                        value = self.is_active( self.r(uu,rr,dd,'active') )
                        if value is not None and (only_active and not value): continue
                        from_unity,from_pv = self.id_expand(self.r(uu,rr,dd,'from_pv'), id_unity=uu)
                        to_unity,to_pv = self.id_expand(self.r(uu,rr,dd,'to_pv'), id_unity=uu)
                        ctrl_unity,ctrl_pv = self.id_expand(self.r(uu,rr,dd,'ctrl_pv'), id_unity=uu)
                        inlet = self.r(uu,rr,dd,'inlet')
                        if from_pv is None:
                            from_pv = ''
                        else:
                            inlet = [ inlet, True][ inlet is None]
                            if from_pv:
                                unity_id_from = from_unity
                                unity_pv_from = from_pv
                            if to_pv:
                                unity_id_to = to_unity
                                unity_pv_to = to_pv
                            if ctrl_pv:
                                unity_id_to = ctrl_unity
                                unity_pv_to = ctrl_pv
                            if unity_id_from == unity_id_to or unity_id_from == uu:
                                unity_id_from = ''
                                if unity_pv_from == unity_pv_to:
                                    unity_pv_from = ''
                            if unity_id_to == uu:
                                unity_id_to = ''
                            uid_from = '<'+unity_id_from+'.'+unity_pv_from
                            uid_to = '>'+unity_id_to+'.'+unity_pv_to
                            if uid_from[1]=='.': uid_from=uid_from.replace('.','')
                            if uid_to[1]=='.': uid_to=uid_to.replace('.','')
                        if len(uid_from)<=1:uid_from = ''
                        if len(uid_to)<=1:uid_to = ''

                        if value is None:
                            value = self.r(uu,rr,dd,'pv')
                            if value is not None:
                                value = '%d'%(value)
                                if self.plant[uu][rr][dd].get('limits') is not None:
                                    value2 = '/' + '%d'%(diff(self.r(uu,rr,dd,'limits')))
                        else:
                            value = ['.',strON][value]

                        if self.r(uu,rr,dd,'type') in ['controller'] and self.r(uu,rr,dd,'mv') is not None:
                            value2 = ' '+'%d'%(self.r(uu,rr,dd,'mv'))

                    else:
                        value = ['.',strON][value]
                    label = self.r(uu,rr,dd,'label')
                    if not label: label = ''

                    header.append([dd,uid_to,uid_from])
                    data.append([value,value2])
                    footer.append(label)
                if header:
                    print('\t',end='')
                    if rr in [ 'procvar']: Nspc = 10
                    else: Nspc = spc_
                    for h in header:
                        fuc = fg.WHITE
                        if uu not in uid_from: fuc = fg.GREEN+st.BRIGHT
                        print(fg.RESET,h[0],fg.BLUE+st.BRIGHT,h[1],fuc,h[2],st.RESET_ALL,sep='',end='')
                        l=sum([len(n) for n in h])
                        print(' '*(Nspc-l),end='')
                    print('')
                    print('\t',end='')
                    for d in data:
                        try:
                            n=eval(d[0])
                        except:
                            n=None
                        if d[0] in [strON]:
                            print(fg.MAGENTA+st.BRIGHT,d[0],st.RESET_ALL,sep='',end='')
                        elif isinstance(n,(int,float)):
                            print(fg.CYAN+st.BRIGHT,d[0],fg.CYAN+st.NORMAL,d[1],st.RESET_ALL,sep='',end='')
                        else:
                            print(fg.WHITE,d[0],fg.CYAN+st.NORMAL,d[1],st.RESET_ALL,sep='',end='')
                            # print(fg.WHITE,d[0],st.RESET_ALL,sep='',end='')
                        l=sum([len(n) for n in d])
                        print(' '*(Nspc-l),end='')
                    print('')

    def print_unity_state(self, *unity):
        """ show all unities of the plant structure 
        """
        if isinstance(unity,dict): unity = list(unity.keys())
        if not unity:
            unity = list(self.r().keys())
        if isinstance(unity,tuple):
            if len(unity) == 1: unity = unity[0]
            if isinstance(unity,str):
                unity = [''.join(unity)]
            unity = list(unity)
        self.print_unity(unity)


    # local function to search state of last linked device
    def linked_actuator(self,to_unity,to_pv):
        """ search for the destination unity given a unity.id origin
            using the from_pv/to_pv data of the actuators
        """
        is_active = True
        actuator = self.r(to_unity,to_pv,'if')
        last_actuator = actuator
        n = 10 # max hops
        while actuator and n>0:
            is_active = is_active and self.is_active( self.r(to_unity,actuator,'active') )
            last_actuator = actuator
            to_unity,to_pv = self.id_expand( self.r(to_unity,actuator,'to_pv'), id_unity=to_unity)
            actuator = self.r(to_unity,to_pv,'if')
            n -= 1
        if n<=0: self.debug_add('if error:',to_unity,to_pv,actuator)
        return last_actuator,is_active,to_unity,to_pv

    # PLANT proccessing rules
    def process(self,dt):
        """ process the plant structure to evolve in time
            contain all the rules for transfering materials between tanks (from_pv/to_pv)
            transfer properties between tanks 
        """
        self.debug = []
        # processa dispositivos da planta
        for uu in self.plant.keys(): # for each unity
            # reset properties of the disabled unity
            if not self.is_active(self.r(uu,'unity',uu,'enabled')):
            # if not self.is_active(self.r(uu+' unity enabled')):
                for yy in self.r(uu,'procvar'): # for each unity procvar
                    if self.r(uu,'procvar',yy,'pv'):# is not None:
                        self.w(uu,yy,'pv', 0)
                        self.r(uu,yy,'sys').pv = 0

            # processa atuadores
            if self.is_active(self.r(uu,'unity',uu,'enabled')) and self.r(uu,'actuator') is not None:
            # if self.is_active(self.r(uu+' unity enabled')) and self.r(uu,'actuator') is not None:
                # loss
                for dd in self.r(uu,'procvar'): # for each procvar
                    if not dd in ['unity'] and 'sys' in self.r(uu,dd):
                        # print('+++ ?',uu,dd)
                        pv_tmp = self.r(uu,dd,'sys').update(dt=dt)
                        self.w(uu,dd,'pv', pv_tmp )

                for dd in self.r(uu,'actuator'): # for each actuator device
                    # to_unity = self.r(uu,dd,'to')
                    inlet = self.r(uu,dd,'inlet')
                    if inlet is None: inlet = True # default

                    # ctrl_pv
                    ctrl_unity,ctrl_pv = self.id_expand( self.r(uu,dd,'ctrl_pv'), id_unity=uu)

                    # from_pv
                    from_unity,from_pv = self.id_expand( self.r(uu,dd,'from_pv'), id_unity=uu)

                    # to_pv
                    to_unity,to_pv = self.id_expand( self.r(uu,dd,'to_pv'), id_unity=uu)

                    # if outlet pv is not specified then default outlet is local unity using same pv
                    if to_pv is None:
                        to_unity = from_unity
                        to_pv = from_pv

                    # if outlet pv is not specified then default outlet is local unity using same pv
                    if ctrl_pv is None:
                        ctrl_unity = to_unity
                        ctrl_pv = to_pv


                    flow = self.r(uu,dd,'flow')
                    if flow is None: flow = 0 # default

                    if from_unity is not None:
                        flow_from = self.r(from_unity,dd,'flow')
                        if flow_from is None: flow_from = 0 # default

                    actuator_type = self.r(uu,dd,'type')

                    mv_from = 0
                    mv_to = 0

                    # actuator is active
                    if self.is_active( self.r(uu,dd,'active') ):
                        if self.r(uu,dd,'type') == 'controller':
                            pv_tmp = self.r(ctrl_unity,ctrl_pv,'pv')
                            mv_tmp = self.r(uu,dd,'mv')
                            ctrl_par = self.r(uu,dd,'ctrl_par')
                            if ctrl_par: # internal actuator PID in auto mode
                                mv = self.r(uu,dd,'ctrl')( pv_tmp ) # match PID and PLC interfaces
                                if mv<0: mv = 0
                                self.w(uu,dd,'mv', mv )
                            else: # a device controller must use wordw_mv to change mv value
                                mv = mv_tmp
                        else:
                            mv = self.MV_MAX
                        if actuator_type in ['transmitter']:
                            pv = self.r(from_unity,from_pv,'pv')
                            pv_tmp = self.r(to_unity,to_pv,'sys').update( dt=dt, var=[pv,0.0])
                            self.w(to_unity,to_pv,'pv', pv_tmp )
                        elif actuator_type in ['controller','relay']:
                            if from_unity == to_unity: # same unity
                                pv_tmp = self.r(from_unity,from_pv,'sys').update( inlet=inlet, dt=dt, mv=mv, var=[flow,0.0])
                                self.w(from_unity,from_pv,'pv', pv_tmp )
                            else: # from a unity to another one
                                mv_from,mv_to = mv,mv
                                flow_from,flow_to = flow,flow
                                if self.r(from_unity,from_pv,'pv') <= min(self.r(from_unity,from_pv,'limits'))+0.1: # CORRIGIR NOISE!!!
                                    mv_from = 0
                                    flow_from = 0
                                    mv_to = 0
                                    flow_to = 0
                                # define state of last linked device, if any
                                if_actuator,is_active,ctrl_to_unity,ctrl_to_pv = self.linked_actuator(to_unity,to_pv)
                                if if_actuator:
                                    to_unity,to_pv = ctrl_to_unity,ctrl_to_pv
                                    if not is_active:
                                        mv_from = 0
                                        flow_from = 0
                                        mv_to = 0
                                        flow_to = 0
                                # from
                                pv_from_tmp = self.r(from_unity,from_pv,'sys').update( inlet=False, dt=dt, mv=mv_from, var=[flow_from,0.0])
                                self.w(from_unity,from_pv,'pv', pv_from_tmp )
                                # to
                                if self.r(to_unity,to_pv,'pv') >= max(self.r(to_unity,to_pv,'limits')): # CORRIGIR NOISE!!!
                                    mv_to = 0
                                    flow_to = 0
                                pv_to_tmp = self.r(to_unity,to_pv,'sys').update( inlet=True, dt=dt, mv=mv_to, var=[flow_to,0.0])
                                self.w(to_unity,to_pv,'pv', pv_to_tmp )
                                if 'filler' in from_unity and 'fc4' in dd:
                                    self.debug_add(from_unity,from_pv,mv_from,pv_from_tmp)
                                    self.debug_add(to_unity,to_pv,mv_to,pv_to_tmp)

                        # search for mixers
                        mixer_active = []
                        for xx in self.r():  # search all unities
                            if self.is_active(self.r(xx,'unity',xx,'enabled')) and self.r(xx,'actuator'): # is unity has actuators
                            # if self.is_active(self.r(xx,'procvar','unity','enabled')) and self.r(xx,'actuator'): # is unity has actuators
                                for yy in self.r(xx,'actuator'):  # search all actuators
                                    if self.r(xx,yy,'type') in ['mixer']: # if actuator is a mixer
                                        if self.is_active( self.r(xx,yy,'active') ): # if mixer is active
                                            mixer_flow = self.r(xx,yy,'flow')
                                            mixer_to,mixer_pv = self.id_expand( self.r(xx,yy,'to_pv'), id_unity=xx)   # mix this procvar
                                            mixer_active.append([mixer_flow,mixer_to,mixer_pv])


                        # transfer properties between unities
                        #
                        mix_proportion = mv_to/self.MV_MAX/10
                        pv_level = None
                        if self.r(to_unity,'procvar'): #and to_unity in self.KEYS['sec']:                        
                            for lvl in self.r(to_unity,'procvar'):
                                if lvl not in self.KEYS['unt'] and 'level' in self.r(to_unity,lvl,'type'):
                                    pv_level = self.r(to_unity,lvl,'pv')
                                # print('+++',to_unity, lvl, pv_level)
                            if pv_level is not None:
                                full_level = diff(self.r(to_unity,lvl,'limits'))
                                mix_proportion *= 1-pv_level/full_level

                        # if not exists mix_pv in from_pv/to_pv!!!!!!!
                        for p in self.r(from_unity,'procvar'):
                            if p not in ['unity',from_pv]: # pv is not unity or itself
                                pv = self.r(from_unity,p,'pv')
                                # mix_pv = self.r(from_unity,p,'mix_pv') # list of pv_ids to mix with
                                # if not mix_pv: mix_pv = ''
                                if pv is not None:
                                    if self.r(to_unity,p,'sys') and mv_from>0:
                                        dt_transf = dt * mix_proportion
                                        for mixer_flow,mixer_to,mixer_pv in mixer_active:
                                            if mixer_active and mixer_to==to_unity and mixer_pv==p:
                                                dt_transf = dt * mix_proportion * mixer_flow
                                        if pv_level is not None and pv_level<0.1: 
                                            dt_transf = pv 
                                            # print('level zero',pv)
                                            # raise Exception('ZERO LEVEL',to_unity,pv_level,self.r(to_unity,'lvl','pv'))
                                        self.r(to_unity,p,'sys').mix_pv(pv,dt_transf)
                                        new_pv = self.r(to_unity,p,'sys').pv
                                        self.w(to_unity,p,'pv', new_pv)


        # atualiza sensores e atuadores
        for uu in self.plant.keys():
            if self.is_active(self.r(uu,'unity',uu,'enabled')):
            # if self.is_active(self.r(uu,'unity enabled')):
                for rr in self.r(uu):
                    if rr not in self.KEYS['sec']: continue
                    for dd in self.r(uu,rr).keys():
                        if 'actuator' in rr:
                            if self.r(uu,rr,dd,'ctrl') is not None:
                                unity_id,pv_id = self.id_expand( self.r(uu,dd,'to_pv'),id_unity=uu )
                                if pv_id is None:
                                    unity_id,pv_id = self.id_expand( self.r(uu,dd,'from_pv'),id_unity=uu ) # ALTERADO from -> to
                                setpoint = self.r(uu,pv_id,'sp')
                                if not setpoint: setpoint = 0
                                self.r(uu,rr,dd,'ctrl').setpoint = setpoint
                                if self.r(uu,rr,dd,'ctrl_par') is not None:
                                    ctrl_par = self.r(uu,rr,dd,'ctrl_par')
                                    self.r(uu,rr,dd,'ctrl').Kp, self.r(uu,rr,dd,'ctrl').Ki, self.r(uu,rr,dd,'ctrl').Kd = ctrl_par
                                    # self.r(uu,rr,dd,'ctrl').reset()
        self.update_ids()
            
        

if __name__ == '__main__':

    clear_screen()
    cfg = load_config('PLANTsim.ini')
    from pyModbusTCP.server import DataBank as db
    plant = Plant()
    plant.load("PLANTsim_LARI_1.plant")

    # raise Exception('STOP')

    MODBUS_mem = Memory()
    db.set_words(0, [0]*24)
    MODBUS_mem.init(db,plant)
    MODBUS_mem.update(db,plant)


    plant.print_process_sequence()
    plant.show_mem_state()

    # plant.print_unity_state(list(plant.r().keys()))
    # plant.print_unity_state('tk2')
    plant.print_unity_state('tk2','tk3')
    # plant.print_unity_state(['tk3'])


    # print('+++ plant tk3.lvl.sp',plant.r('tk3.lvl.sp'))

    # plant.print_unity_state()

    # plant.print_file("PLANTsim_LARI_1.plant")
    # plant.print_process_sequence()
