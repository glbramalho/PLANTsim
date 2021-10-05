#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PLANTsim: process SIMULATOR FOR INDUSTRIAL AUTOMATION PLANTS

Features:
    - PID controller simulation (see PID() )
    - sub-system simulation by user-function call-backs (provided: generic(), hydraulic() )
    - MODBUS TCP data transfer (MASTER/SLAVE)
    - User defined plants (.plant)
    - Programable events (.sim)
    - GRAFCET language (.prg)

Created on Wed Mar 10 15:27:30 2021

@author: glbramalho@gmail.com - Geraldo Ramalho

TODO save_SYS("PID_MODBUS_SYS.txt",plant) # should save the state to continue simulation from a saved point
TODO implement the physics of transport (non linearities): flow, filling, heating
TODO read a file with adjusts to the setpoints and PID gains
TODO plant.show... must read word memory size from .ini
TODO fuzzy control
TODO graphical interface
TODO machine learning
TODO web interface (cloud enable)
DONE digital twin concept - LARI process plant 1
DONE improve visual interface - colored
"""

import time

from pyModbusTCP.client import ModbusClient
from pyModbusTCP.server import ModbusServer
from pyModbusTCP.server import DataBank as db

from PLANTsim_PLANT import Plant
from PLANTsim_MEMORY import Memory as mem
from PLANTsim_SIMULATION import Events as events
from PLANTsim_GRAFCET import Program as prg
from PLANTsim_UTIL import load_config
from PLANTsim_UTIL import clear_screen 
from PLANTsim_UTIL import hm
from PLANTsim_UTIL import Status_Bar


DEBUG_ENABLED = True
status_bar = Status_Bar()

simb_anim = [1]+list(' :')

################################### MAIN
##
###################################
#
VERSION = '0.1'
INIFILE = 'PLANTsim.ini'
cfg = load_config(INIFILE)

interface_mode = cfg.get('interface_mode')
if not interface_mode:
    interface_mode = 0
#
simulation = events()
if cfg.get('sim_execute') and cfg.get('sim_file'):
    simulation.load(cfg.get('sim_file'))    

program = prg()
if cfg.get('prg_execute') and cfg.get('prg_file'):
    program.load(cfg.get('prg_file'))

# definicoes da planta ------------------------------------------------------------
plant = Plant()
plant_file = cfg.get('plant_file')
plant.load(plant_file)

#
clear_screen()

# MODBUS master
SLAVE_ADDR = 1
if not simulation.is_run and not program.is_run:
    master = ModbusClient(timeout=3)
    master.host(cfg.get('slave_ip'))
    master.port(cfg.get('slave_port', 502))
    master.unit_id(cfg.get('slave_addr'))

# try to connect MODBUS
if not simulation.is_run and not program.is_run:
    print("Trying to connect to MODBUS slave...")
    if not master.is_open():
        if not master.open():
            print("*** unable to connect to "+
                  cfg.get('slave_ip')+":"+str(cfg.get('slave_port')))
        else:
            msgIP = "{}".format(cfg.get('slave_ip'))
            print("MODBUS master is connected to IP {} port {}".format(msgIP,
                                                                       cfg.get('slave_port')))

if not simulation.is_run and not program.is_run:
    if not master.open():
        print("Trying to connect to a MODBUS master...")
        # Create an instance of ModbusServer (para uso com SCADA mestre)
        slave = ModbusServer(host='', port=cfg.get('server_port'), no_block=True)

# 16bit Sensor (offset=0), 16 bit Act (offset=2), 20 words (offset=4)
memory_length = (cfg.get('bit_length',
                 cfg.get('bit_length', 32))//16) * 2 + cfg.get('word_length',
                 cfg.get('word_length', 16)) * 2
db.set_words(cfg.get('memory_ini_addr', 0), [0]*memory_length)
#
memory = mem()
memory.set_addr(cfg.get('bit_s_addr', 0),cfg.get('bit_a_addr', 2),
                cfg.get('bit_length', 32),
                cfg.get('word_s_addr', 4),cfg.get('word_a_addr', 20),
                cfg.get('word_length', 16) )
memory.init(db,plant)

bitsS,bitsA,wordsS,wordsA = (None,None,None,None)

# Timing
start_time = time.time()
last_time = start_time

# System Runtime
elapsed_time = 0
show_time = 0
update_comm_time = 0

# Timeout
PRG_TIMEOUT = cfg.get('prg_timeout', 5*60)
SIM_TIMEOUT = cfg.get('sim_timeout', 5*60)
COMM_TIMEOUT = cfg.get('comm_timeout', 5*60)
if not simulation.is_run and not program.is_run:
    execution_timeout = COMM_TIMEOUT # seconds
elif simulation.is_run:
    execution_timeout = SIM_TIMEOUT # seconds
elif program.is_run:
    execution_timeout = PRG_TIMEOUT # seconds
timeout = execution_timeout

##----
state_changed = False
stop_process = False
cycle_count = 0

# 
if simulation.is_run and not simulation.verify(plant):
    stop_process = True
if program.is_run and not program.verify(plant):
    stop_process = True
    
# Open SLAVE (server)
try:
    # if not master.is_open():
    print("Start MODBUS slave...")
    if not simulation.is_run and not program.is_run and 'slave' in locals():
        slave.start()

    print("Running process...")
    while not stop_process: # while time.time() - start_time < 300:

        status_bar.clear()
        status_bar.add('title','PLANTsim v'+VERSION)

        # status = ['PLANTsim v'+VERSION,'T/O'+simb_anim[simb_anim[0]]+'%ds'%(execution_timeout)]
        if execution_timeout > 60:
            bar = hm(execution_timeout)
        else:
            bar = 'T/O'+simb_anim[simb_anim[0]]*int(execution_timeout/timeout*12)
        status_bar.add('warning','%s'%(bar))

        #Setting the time variable dt
        current_time = time.time()
        dt = (current_time - last_time)
        elapsed_time += dt
        cycle_count += 1

        # status.append('%4d'%(elapsed_time))
        status_bar.add('info','%dcps'%(cycle_count/elapsed_time))

        execution_timeout -= dt
        if execution_timeout<0:
            stop_process = True
            status_bar.clear()
            status_bar.add('warning','.'*85+'TIME OUT')
            status_bar()
            DEBUG_ENABLED = False
            raise Exception('TIME OUT')


        # MASTER-SLAVE COMM
        if not simulation.is_run and not program.is_run and \
            'master' in locals() and master.is_open():
            status_bar.add('comm','MASTER connected to {}:{} '.format(cfg.get('slave_ip'),
                                                               cfg.get('slave_port')))
            if elapsed_time > update_comm_time:
                update_comm_time = elapsed_time + 2
                # read from SLAVE
                bitsA = master.read_coils(memory.BITS_MAX_LEN,memory.BITS_MAX_LEN)
                wordsA = master.read_holding_registers(memory.WORDS_MAX_LEN,
                                                       memory.WORDS_MAX_LEN)
                # write do SLAVE
                if bitsS: master.write_multiple_coils(0,bitsS)
                if wordsS: master.write_multiple_registers(0,wordsS)
                status_bar.add('txrx','TX')
            # update memory
            bitsS = memory.read_bitsS(db)
            wordsS = memory.read_wordsS(db)
            if bitsA: memory.write_bitsA(db,bitsA)
            if wordsA: memory.write_wordsA(db,wordsA)

        if not simulation.is_run and not program.is_run and \
            'slave' in locals() and slave.is_run:
            status_bar.add('comm','SLAVE listening on port {}'.format(cfg.get('server_port')))

        if memory.state_changed:
            state_changed = True

        if state_changed:
            if not simulation.is_run and not program.is_run:
                execution_timeout = COMM_TIMEOUT
                status_bar.add('txrx',' RX ')

        if simulation.is_run:
            sim_status = simulation.update(plant,memory,db,elapsed_time)
            memory.setmem(db,plant)
            status_bar.add('prg',' events time:%d'%(int(elapsed_time)))
            # for s in sim_status: status.append(s)

        if program.is_run:
            prg_status = program.execute(plant,memory,db,dt)  
            memory.setmem(db,plant)
            status_bar.add('prg',' GRAFCET Active Steps: '+' '.join([str(s[0]) for s in prg_status if s[1]]) )

        plant.update_params()


        # PROCESSAMENTO DA PLANTA
        plant.process(dt)
        memory.update(db,plant)

        last_time = current_time

        if plant.r('* actuator reset active'):
            status_bar.add('warning','Reloading Plant...')
            plant.load(cfg.get('plant_file'))

        if plant.r('* actuator shutdown active'):
            stop_process = True
            status_bar.clear()
            status_bar.add('warning','_'*85+'SHUTDOWN')
            status_bar()
            elapsed_time = 0
            DEBUG_ENABLED = False
            raise Exception('SHUTDOWN')

        # show user interface
        if elapsed_time > show_time:
            status_bar.add('title',plant_file)
            
            show_time = elapsed_time + 1
            state_changed = False
            simb_anim[0] += 1
            if simb_anim[0]>len(simb_anim)-1: simb_anim[0]=1

            # LOG
            if cfg.get('save_log'):
                memory.save_log(cfg.get('log_file'),db,elapsed_time)

            # VERBOSE
            if cfg.get('verbose', True):
                clear_screen()
                display = interface_mode
                if interface_mode == 9:
                    display = int(elapsed_time) % 3
                if display == 0:
                    plant.show_mem_state()
                elif display == 1:
                    plant.show_mem_state()
                    plant.print_process_sequence()
                elif display == 2:
                    plant.print_unity_state()
                                
            
            if simulation.is_run and simulation.debug:
                for m in simulation.debug:
                    status_bar.add('debug',m)

            if program.is_run and program.debug:
                for m in program.debug:
                    status_bar.add('debug',m)

            if memory.debug:
                for m in memory.debug:
                    status_bar.add('debug',m)

            if plant.debug:
                for m in plant.debug:
                    status_bar.add('debug',m)
                memory.print_mem(db)
                stop_process = True
                if plant.shutdown: raise Exception('Plant Error!')

            status_bar()


# except:
except Exception as e_code:
    stop_process = True
    if 'slave' in locals() and slave.is_run:
        print("Shutdown MODBUS slave...")
        slave.stop()
        print("MODBUS slave is offline")
    if 'master' in locals() and master.is_open():
        print("Shutdown MODBUS master...")
        master.close()
        print("MODBUS master is offline")

    if 'e_code' in locals():
        import sys
        import os

        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        if DEBUG_ENABLED:
            print('>>>',e_code,exc_type, 'line', exc_tb.tb_lineno)
            import traceback
            traceback.print_exc()
            # import pdb
            # pdb.post_mortem(exc_tb) # open debug
finally:
    stop_process = True
    if 'slave' in locals():
        slave.stop()
    if 'master' in locals():
        master.close()
    print('PLANTsim finished!')
    