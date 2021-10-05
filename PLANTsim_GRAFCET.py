#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 19 09:29:29 2021

@author: glbramalho@gmail.com - Geraldo Ramalho
"""

import csv
from colorama import Fore as fg, Back as bg, Style as st

from numpy import random, exp
# import numpy as np
from datetime import datetime
# from PROCSIM import PID # used for the plant structure
from PLANTsim_UTIL import *
from PLANTsim_MEMORY import Memory
from PLANTsim_PLANT import Plant

################################### GRAFCET INTERPRETER
##
###################################
class Program:
    def __init__(self):
        self.PRG = {}
        self.is_run = False
        self.debug = []

    def debug_add(self, *args):
        self.debug.append(args)
                
    def load(self,file_name):
        import re
        cmds = []
        # CSV file with header
        with open(file_name) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=' ')
            step = 0
            initial_step = 'True'
            for row in csv_reader:
                row = [ x for x in row if len(x)>0]
                if row and row[0] not in '#':
                    row = (' '.join(row)).lower()
                    row=row.replace('false','False')
                    row=row.replace('true','True')
                    # print('+++ row = ',row,'=>','step'in row,'action' in row,'transition'in row)
                    at_time = 'step_time_count>=0'
                    condition = 'True'
                    if 'step' in row.split(' ')[0]:
                        if 'True' not in row and 'False' not in row: row += ' False'                       
                        _,step,initial_step = re.split(';  | ',row)
                        initial_step.strip()
                        cmds.append(['step',step,initial_step])
                    elif 'action'in row.split(' ')[0]:
                        # print('+++', row, 'end in row','end'  in row)
                        actions = ''                    
                        if 'cont' in row.split(' ')[1]:
                            row=row.replace('cont','if True then')
                            # print('++++++ row',row)
                            _,condition,actions = re.split(';  |if |then ',row)
                        elif 'begin' in row.split(' ')[1]:
                            if 'if' in row and 'then' in row:
                                row=row.replace('begin','at step_time_count<0')
                                _,at_time,condition,actions = re.split(';  |at |if |then ',row)
                            else:
                                row=row.replace('begin','at step_time_count<0 then ')
                                _,at_time,actions = re.split(';  |at |then ',row)
                        elif 'delay' in row.split(' ')[1]:
                            if 'if' in row and 'then' in row:
                                row=row.replace('delay','at step_time_count>')
                                _,at_time,condition,actions = re.split(';  |at |if |then ',row)
                            else:
                                x = row.split(' ')
                                while x[0] not in 'delay': x.pop(0)
                                value = x[1].strip()
                                row=row.replace('delay','at step_time_count>'+value+' then ')
                                _,at_time,actions = re.split(';  |at |then ',row)
                        elif 'timed' in row.split(' ')[1]:
                            if 'if' in row and 'then' in row:
                                row=row.replace('timed','at step_time_count<')
                                _,at_time,condition,actions = re.split(';  |at |if |then ',row)
                            else:
                                x = row.split(' ')
                                while x[0] not in 'timed': x.pop(0)
                                value = x[1].strip()
                                row=row.replace('timed','at step_time_count<'+value+' then ')
                                _,at_time,actions = re.split(';  |at |then ',row)
                        elif 'end' in row.split(' ')[1]:
                            if 'if' in row and 'then' in row:
                                row=row.replace('end','at step_transition_fired')
                                _,at_time,condition,actions = re.split(';  |at |if |then ',row)
                            else:
                                row=row.replace('end','at step_transition_fired then ')                                
                                _,at_time,actions = re.split(';  |at |then ',row)
                        elif 'if' in row.split(' ')[1] and 'then' in row:
                            _,condition,actions = re.split(';  |if |then ',row)
                                
                        at_time = at_time.strip()
                        condition = condition.strip()
                        actions = re.split(';  |, ',actions)
                        actions = [x.strip() for x in actions]
                        cmds.append(['action',at_time,condition,actions])

                    elif 'transition' in row.split(' ')[0] and 'from' in row and 'to' in row:
                        _,from_step,to_step,condition = re.split(';  |from |to |if ',row)
                        from_step = from_step.strip()
                        to_step = to_step.strip()
                        cmds.append(['transition',from_step,to_step,condition])
                                                
        # except:
        #     self.debug_add('*** GRAFCET.load: Unable to read .grafcet file.')
        #     self.is_run = False
                            
        # mount program dictionary        
        self.PRG = {}
        for command in cmds:
            if 'step' in command[0]:                
                _,step,initial_step = command
                step_number = eval(step)
                step_active = eval(initial_step)
                self.PRG[step_number] = {'active':step_active, 'time_count':-1, 'transition_fired':False,
                                         'actions':[],
                                         'transition':{'enabled':step_active, 'from':None, 'to':None, 'receptivity':None} 
                                         }
            if 'action' in command[0]:                
                _,at_time,condition,actions = command
                action_condition = at_time +' and '+ condition
                self.PRG[step_number]['actions'].append([action_condition,actions])
            if 'transition' in command:               
                _,from_step,to_step,transition_receptivity = command
                transition_from = eval(from_step)
                transition_to = eval(to_step)
                if not isinstance(transition_from,tuple): transition_from = [transition_from]
                if not isinstance(transition_to,tuple): transition_to = [transition_to]
                self.PRG[step_number]['transition']['receptivity'] = transition_receptivity
                self.PRG[step_number]['transition']['from'] = transition_from
                self.PRG[step_number]['transition']['to'] = transition_to
                for f in transition_from:
                    if self.PRG[f]['transition']['from'] is None: self.PRG[f]['transition']['from'] = transition_from
                    if self.PRG[f]['transition']['to'] is None: self.PRG[f]['transition']['to'] = transition_to
                    if self.PRG[f]['transition']['receptivity'] is None: self.PRG[f]['transition']['receptivity'] = transition_receptivity

        self.is_run = True

    def parse_action_condition(self,plant,condition,step):
        # print('+++',condition)
        condition = condition.replace('step_active',str(self.PRG[step]["active"]))
        condition = condition.replace('step_time_count',str(self.PRG[step]["time_count"]))
        condition = condition.replace('step_transition_fired',str(self.PRG[step]["transition_fired"]))
        condition = condition.replace('step',str(step))
        # print('+++ parse condition=',condition)
        return plant.is_active(condition)
            # self.debug_add('*** invalid expression:',ev)
            # self.is_run = False

    def verify(self,plant):
        plant.update_ids()
        for step in self.PRG:
            for condition,actions in self.PRG[step]['actions']:
                for action in actions:
                    # print('+++ action=',action)
                    var,ev = action.split('=')
                    ev = plant.eval_exp(ev)
                    if plant.r(var) is None:
                        print('SIM: Invalid id:',var, 'in action',action)
                        return False
            receptivity = self.PRG[step]['transition']['receptivity']
            if plant.eval_exp(receptivity) is None:
                print('SIM: Invalid receptivity:',receptivity)
                return False
        return True

    def execute(self,plant,mem,DB,delta_time=0.1):
        # program interpretation
        # print('+++ EXECUTE: plant=',plant.r('tk2.lvl.pv'),plant.r('pip23.fv23.active') )
        for step in self.PRG:
            # print('+++ EXECUTE: time_count=',self.PRG[step]["time_count"])
            
            if self.PRG[step]['active']:
                self.PRG[step]["time_count"] = self.PRG[step]["time_count"] + delta_time
                # execute actions including END
                for condition,actions in self.PRG[step]['actions']:
                    if self.parse_action_condition(plant,condition,step): 
                        for action in actions:
                            # print('+++ action=',action)
                            var,ev = action.split('=')
                            ev = plant.eval_exp(ev)
                            plant.w(var, ev)
                            # print('+++ condition=',condition, 'action=',action,ev)
                    
                # deactivate step
                if self.PRG[step]['transition_fired']:
                    # print('+++ step',step,'DEACTIVATED')
                    self.PRG[step]['active'] = False
                    self.PRG[step]['transition_fired'] = False
                    self.PRG[step]['time_count'] = -0.1

        # enable transitions
        for step in self.PRG:
            self.PRG[step]['transition']['enabled'] = self.PRG[step]['active']
            # print('+++ step',step,'transition enabled = ',self.PRG[step]['active'])
                
        # fire transitions
        for step in self.PRG:
            if self.PRG[step]['transition']['enabled']:
                receptivity = self.PRG[step]['transition']['receptivity']
                if plant.eval_exp(receptivity):
                    # print('+++ step',step,'fire transition')
                    for f in self.PRG[step]['transition']['from']:
                        self.PRG[f]['transition_fired'] = True
                        # print('+++ step',f,'transition fired')
                    for t in self.PRG[step]['transition']['to']:
                        self.PRG[t]['active'] = True
        return [(step,self.PRG[step]['active']) for step in self.PRG]

                        
    def show(self,plant):
        for step in self.PRG:
            active = self.PRG[step]['active']
            light = [fg.WHITE,fg.RESET][ active ]
            print(light,'Step',fg.CYAN+st.BRIGHT,step,fg.MAGENTA,['','ACTIVE'][active],st.RESET_ALL)
            print(light,'  actions')
            for action in self.PRG[step]['actions']:
                condition = self.parse_action_condition(action[0],step)
                cond_val = ['','<- TRUE'] [  condition ]
                cond_val = ''
                bright = ['',st.BRIGHT] [  condition ]
                # print('+++ condition=',condition)
                print('    if',fg.GREEN+bright,action[0],fg.MAGENTA,cond_val,fg.RESET, 'then',fg.YELLOW,action[1:],st.RESET_ALL)
            enabled = self.PRG[step]['transition']['enabled']
            light = [fg.WHITE,fg.RESET][ enabled ]
            print(light,'  transition',fg.MAGENTA+st.BRIGHT,['', 'ENABLED'][enabled],st.RESET_ALL)
            from_step = list(self.PRG[step]['transition']['from'])
            to_step = list(self.PRG[step]['transition']['to'])
            receptivity = self.PRG[step]['transition']['receptivity']
            rec_val = ['','<- TRUE'] [  plant.eval_exp(receptivity) ]
            rec_val = ''
            bright = ['',st.BRIGHT] [plant.eval_exp(receptivity)]
                # print('   ',transition,fg.GREEN+st.BRIGHT,receptivity,fg.RESET,tmp,self.PRG[step]['transition'][transition])
            print(light,'    from',fg.CYAN+bright,from_step,fg.RESET,'to',fg.CYAN,to_step,st.RESET_ALL)
            print(light,'    receptivity',fg.GREEN+bright,receptivity,fg.MAGENTA,rec_val,st.RESET_ALL)
                
        
                        
if __name__ == '__main__':

    clear_screen()
    cfg = load_config('PLANTsim.ini')
    from pyModbusTCP.server import DataBank as db
    plant = Plant()
    plant.load("PLANTsim_LARI_1.plant")
    
    memory = Memory()
    db.set_words(0, [0]*24)    
    memory.init(db,plant)
    memory.update(db,plant)
    
    
    program = Program()
    print('Program:',cfg.get('prg_file'))
    program.load(cfg.get('prg_file'))
    dt = 0.5
    if not program.verify(plant):
        print('PROGRAM error!')
    else:
        dados=[]
        for x in range(0,100):
            program.execute(plant,memory,db,dt)
                
            # PROCESSAMENTO DA PLANTA                    
            # plant.update_params()
            plant.process(dt)
            # clear_screen()
            dados.append([x,plant.r('tk0.lvl.pv'), plant.r('tk2.fc02.active'),plant.r('tk2.lvl.pv'),plant.r('pip23.fv23.active'),plant.r('tk3.lvl.pv')])
    
        for d in dados:
            print(d)        
    # plant.show_mem_state()
    # program.show(plant)
    # print('+++plant tk3.level.sp',plant.r('tk3.level.sp'))
