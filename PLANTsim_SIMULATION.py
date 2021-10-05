#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 19 09:29:29 2021

@author: glbramalho@gmail.com - Geraldo Ramalho
"""

import csv
from numpy import random, exp
# import numpy as np
# from datetime import datetime
# from CTRL_PID import PID # used for the plant structure
from PLANTsim_UTIL import *
from PLANTsim_MEMORY import Memory
from PLANTsim_PLANT import Plant


################################### EVENT SIMULATION 
##
###################################
class Events:
    def __init__(self):
        self.INS = []
        self.is_run = False
        self.debug = []

    def debug_add(self, *args):
        self.debug.append(args)
                
    def load(self,file_name):      
        self.INS = []
        try:
            # CSV file with header
            with open(file_name) as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=' ')
                for row in csv_reader:
                    if row and  row[0] not in '# ':
                        self.INS.append(row)
            self.is_run = True
        except:
            self.debug_add('Unable to read .sim file.')
            self.is_run = False   
        
            
    def verify(self,plant):
        stat = []
        plant.update_ids()
        for instruction in self.INS:
            if '#' in instruction[0]: continue
            while '' in instruction: instruction.remove('')
            exp,cmd = instruction[1:]
            var,val=cmd.split('=')
            if plant.eval_exp(exp) is None:
                print('SIM: Invalid expression:',exp, 'in',instruction)
                return False
            if plant.r(var) is None:
                print('SIM: Invalid id:',var, 'in',instruction)
                return False
            try:
                val = plant.eval_exp(val)
            except:
                print('SIM: Invalid value:',val, 'in',instruction)
                return False
        return True
                
    def update(self,plant,MODBUS_mem,DataBank,elapsed_time):
        stat = []
        plant.update_ids()
        for instruction in self.INS:
            if '#' in instruction[0]: continue
            while '' in instruction: instruction.remove('')
            exp,cmd = instruction[1:]
            var,val=cmd.split('=')
            if exp.upper() in ['FALSE','TRUE']: 
                exp = exp.capitalize()
            if val.upper() in ['FALSE','TRUE']: 
                val = val.capitalize()
            if plant.r(var) is None:
                raise Exception('SIM: Invalid id:',var, 'in',exp,cmd)
            try:
                val = eval(val)
            except:
                self.debug_add('value error',instruction)
                self.is_run = False
            nm = var.split('.')
            if instruction[0] in 'if':
                condition = plant.eval_exp(exp)
                if condition: 
                    plant.w(var, val)
                    stat.append(var+'='+str(val))
            elif instruction[0] in 'at':
                prg_time = eval(exp)
                if int(elapsed_time) == prg_time:                     
                    plant.w(var, val)      
                    stat.append(var+'='+str(val))
        return stat

                        
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

    simulation = Events()
    simulation.load(cfg.get('sim_file'))
    print('verify=',simulation.verify(plant))
    sim_status = simulation.update(plant,memory,db,1)

