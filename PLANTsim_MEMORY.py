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
# from CTRL_PID import PID # used for the plant structure
from PLANTsim_UTIL import *

################################### MEMORY HANDLING
##
##
###################################

class Memory:
    def __init__(self):
        self.ADDR_INI = 0
        self.BITS_S_OFFSET = 0
        self.BITS_A_OFFSET = 2
        self.WORDS_S_OFFSET = 4
        self.WORDS_A_OFFSET = 20
        self.BITS_MAX_LEN = 32
        self.WORDS_MAX_LEN = 16
        self.state = []
        self.state_changed = False
        self.WNBITS = 12 # max number of bits
        self.MAXWVAL = 2**self.WNBITS-1 # max word value
        self.debug = []
        self.print_mem_state = []

    def to_mem_value(self,value,limits=None):
        if limits is None: limits=[0,100]
        return int(value / diff(limits) * (self.MAXWVAL))

    def from_mem_value(self,value,limits=None):
        if limits is None: limits=[0,100]
        return min(value / (self.MAXWVAL) * diff(limits), limits[1] )
    
    # @property
    def debug_print(self):
        print('>>> MEM debug:',end=' ')
        for dl in self.debug:
            for d in dl:
                print(d,end=' ')
        print('')

    # @debug.setter
    def debug_add(self, *args):
        self.debug.append(args)
    
    def set_addr(self,bit_s_offset,bit_a_offset,bit_length,word_s_offset,word_a_offset,word_length):
        self.BITS_S_OFFSET = bit_s_offset                          # 32 bits (2 words)
        self.BITS_A_OFFSET = bit_a_offset    # 32 bits (2 words)
        self.WORDS_S_OFFSET = word_s_offset   # 16 words
        self.WORDS_A_OFFSET = word_a_offset     # 16 words
        self.BITS_MAX_LEN = bit_length # 32 bits
        self.WORDS_MAX_LEN = word_length # 16 words
        
    def word2bit(self,words):
        bits = []
        for w in words:
            b = []
            while w>0: 
                b.append(w%2==1)
                w=w>>1
            b += [False]*((self.BITS_MAX_LEN//2) - len(b))
            bits += b
        return bits
    
    def bit2word(self,bits):
        if len(bits)>16:
            words = [bits[:16],bits[16:]]
        else:
            words = [bits]
        
        ret = []
        for n,word in enumerate(words):
            w = 0
            for i,b in enumerate(word):
                if b: w += 2**i
            ret.append(w)
        return ret
    
    ##---- atualiza memorias com valores do plant
    def read_wordsS(self,db):
        words = db.get_words(self.ADDR_INI+self.WORDS_S_OFFSET,self.WORDS_MAX_LEN)
        return words

    def read_wordsA(self,db):
        return db.get_words(self.ADDR_INI+self.WORDS_A_OFFSET, self.WORDS_MAX_LEN)
        
    def write_wordsA(self,db,words):
        db.set_words(self.ADDR_INI+self.WORDS_A_OFFSET, words)

    def read_bitsS(self,db):
        words = db.get_words(self.ADDR_INI+self.BITS_S_OFFSET,self.BITS_MAX_LEN//16)
        return self.word2bit(words)

    def read_bitsA(self,db):
        return self.word2bit(db.get_words(self.ADDR_INI+self.BITS_A_OFFSET, self.BITS_MAX_LEN//16))

    def write_bitsA(self,db,bits):
        words = self.bit2word(bits)
        db.set_words(self.ADDR_INI+self.BITS_A_OFFSET, words)

    ##---- update memory to plant
    def update(self,db,plant):
        old_state = self.state
        bitsS = [False]*self.BITS_MAX_LEN
        bitsA = self.word2bit(db.get_words(self.ADDR_INI+self.BITS_A_OFFSET,self.BITS_MAX_LEN//16))
        wordsS = db.get_words(self.ADDR_INI+self.WORDS_S_OFFSET,self.WORDS_MAX_LEN)
        wordsA = db.get_words(self.ADDR_INI+self.WORDS_A_OFFSET,self.WORDS_MAX_LEN)
        for uu in plant.plant.keys():
            for rr in plant.r(uu):
                for dd in plant.r(uu,rr):
                    yy = 'enabled' if dd in ['unity'] else 'active'
                    bit_addr = plant.r(uu,rr,dd,'bit')
                    if rr in ['sensor','procvar']:              
                        if bit_addr is not None: bitsS[bit_addr] = plant.is_active( plant.r([uu,rr,dd,yy]) )
                    if rr in ['actuator','procvar']:   
                        # bit
                        if bit_addr is not None: plant.w(uu,rr,dd,yy, bitsA[bit_addr] )
                        # word
                        word_list = plant.words_addr(uu,rr,dd)
                        if word_list:
                            for zz,write,ww in word_list:
                                word_addr = plant.r([uu,rr,dd,zz])
                                limits = plant.r([uu,rr,dd,'limits'])
                                if write:
                                    plant.w(uu,rr,dd,ww, self.from_mem_value(wordsA[word_addr],limits) )
                                else:
                                    wordsS[word_addr] = self.to_mem_value(plant.r(uu,rr,dd,ww), limits)                            
        db.set_words(self.ADDR_INI+self.BITS_S_OFFSET, self.bit2word(bitsS) )
        db.set_words(self.ADDR_INI+self.WORDS_S_OFFSET, wordsS)
        
        
        self.state = bitsA+wordsA
        if old_state:
            lst = [i != j for i, j in zip(self.state, old_state)]
            self.state_changed = any(lst)        

    ##---- load memory with the plant devices values
    def load(self,db,plant):
        old_state = self.state            
        bitsS = [False]*self.BITS_MAX_LEN
        bitsA = self.word2bit(db.get_words(self.ADDR_INI+self.BITS_A_OFFSET,self.BITS_MAX_LEN//16))
        wordsS = db.get_words(self.ADDR_INI+self.WORDS_S_OFFSET,self.WORDS_MAX_LEN)
        wordsA = db.get_words(self.ADDR_INI+self.WORDS_A_OFFSET,self.WORDS_MAX_LEN)
        for uu in plant.plant.keys():
            for rr in plant.r(uu):
                for dd in plant.r(uu,rr):
                    yy = 'enabled' if dd in ['unity'] else 'active'
                    bit_addr = plant.r(uu,rr,dd,'bit')
                    if rr in ['sensor','procvar']:                        
                        if plant.r(uu,rr,dd,'bit') is not None: bitsS[plant.r(uu,rr,dd,'bit')] = plant.is_active( plant.r([uu,rr,dd,yy]) )
                    if rr in ['actuator','procvar']:   
                        if bit_addr is not None: plant.w(uu,rr,dd,yy, bitsA[bit_addr] )
                        word_list = plant.words_addr(uu,rr,dd)
                        if word_list:
                            for zz,write,ww in word_list:
                                word_addr = plant.r([uu,rr,dd,zz])
                                limits = plant.r([uu,rr,dd,'limits'])
                                if write:
                                    plant.w(uu,rr,dd,ww, self.from_mem_value(wordsA[word_addr],limits))
                                else:
                                    wordsS[word_addr] = self.to_mem_value(plant.r(uu,rr,dd,ww), limits)                          
        db.set_words(self.ADDR_INI+self.BITS_S_OFFSET, self.bit2word(bitsS) )
        db.set_words(self.ADDR_INI+self.BITS_A_OFFSET, self.bit2word(bitsA) )
        db.set_words(self.ADDR_INI+self.WORDS_S_OFFSET, wordsS)
        db.set_words(self.ADDR_INI+self.WORDS_A_OFFSET, wordsA)
        
        self.state = bitsA+wordsA
        if old_state:
            lst = [i != j for i, j in zip(self.state, old_state)]
            self.state_changed = any(lst)
        
        # NAO APAGAR!!!
        # 14bits=16384 => 0.00 a 9.999
        # 1 word no scada (n=0-2 k=0-16383) com script: w = (n<<14)+k
        # k = plant[uu][ plant[uu]['actuator'][dd]['pv_id'] ]['k']
        # n = (w>>14) & 3
        # if n<3:
        #   k[n] = w&(2**14-1)                                
        #   plant[uu][ plant[uu]['actuator'][dd]['pv_id'] ]['k'] = k

    ##---- set all memories using the plant values
    def setmem(self,db,plant):
        old_state = self.state            
        bitsS = [False]*self.BITS_MAX_LEN
        bitsA = self.word2bit(db.get_words(self.ADDR_INI+self.BITS_A_OFFSET,self.BITS_MAX_LEN//16))
        wordsS = db.get_words(self.ADDR_INI+self.WORDS_S_OFFSET,self.WORDS_MAX_LEN)
        wordsA = db.get_words(self.ADDR_INI+self.WORDS_A_OFFSET,self.WORDS_MAX_LEN)
        for uu in plant.plant.keys():
            for rr in plant.r(uu):
                for dd in plant.r(uu,rr):
                    yy = 'enabled' if dd in ['unity'] else 'active'
                    bit_addr = plant.r(uu,rr,dd,'bit')
                    if rr in ['sensor','procvar']:                        
                        if plant.r(uu,rr,dd,'bit') is not None: 
                            bitsS[bit_addr] = plant.is_active( plant.r([uu,rr,dd,yy]) )
                    if rr in ['actuator','procvar']:   
                        if bit_addr is not None: 
                            bitsA[bit_addr] = plant.is_active( plant.r([uu,rr,dd,yy]) )
                        word_list = plant.words_addr(uu,rr,dd)
                        if word_list:
                            for zz,write,ww in word_list:
                                word_addr = plant.r([uu,rr,dd,zz])
                                limits = plant.r(uu,rr,dd,'limits')
                                value = self.to_mem_value(plant.r(uu,rr,dd,ww),limits)
                                if write:
                                    wordsA[word_addr] = value                            
                                else:
                                    wordsS[word_addr] = value                           
        db.set_words(self.ADDR_INI+self.BITS_S_OFFSET, self.bit2word(bitsS) )
        db.set_words(self.ADDR_INI+self.BITS_A_OFFSET, self.bit2word(bitsA) )
        db.set_words(self.ADDR_INI+self.WORDS_S_OFFSET, wordsS)
        db.set_words(self.ADDR_INI+self.WORDS_A_OFFSET, wordsA)
        
        self.state = bitsA+wordsA
        if old_state:
            lst = [i != j for i, j in zip(self.state, old_state)]
            self.state_changed = any(lst)
        
            
    ##---- inicializa memorias com valores do plant
    def init(self,db,plant): 
        bitsS = [False]*self.BITS_MAX_LEN
        bitsA = [False]*self.BITS_MAX_LEN
        wordsS = [0]*self.WORDS_MAX_LEN
        wordsA = [0]*self.WORDS_MAX_LEN
        for uu in plant.plant:
            for rr in plant.r(uu):
                for dd in plant.r(uu,rr):
                    yy = 'enabled' if dd in ['unity'] else 'active'
                    bit_addr = plant.r(uu,rr,dd,'bit')
                    if rr in ['sensor','procvar']:                        
                        if plant.r(uu,rr,dd,'bit') is not None: bitsS[plant.r(uu,rr,dd,'bit')] = plant.r([uu,rr,dd,yy])
                    if rr in ['actuator','procvar']:   
                        if bit_addr is not None: plant.w(uu,rr,dd,yy, bitsA[bit_addr] )
                        word_list = plant.words_addr(uu,rr,dd)
                        if word_list:
                            for zz,write,ww in word_list:
                                word_addr = plant.r([uu,rr,dd,zz])
                                limits = plant.r([uu,rr,dd,'limits'])
                                if write:
                                    plant.w(uu,rr,dd,ww, self.from_mem_value(wordsA[word_addr],limits))
                                else:
                                    wordsS[word_addr] = self.to_mem_value(plant.r(uu,rr,dd,ww),limits)
        db.set_words(self.ADDR_INI+self.BITS_S_OFFSET, self.bit2word(bitsS) )
        db.set_words(self.ADDR_INI+self.BITS_A_OFFSET, self.bit2word(bitsA) )
        db.set_words(self.ADDR_INI+self.WORDS_S_OFFSET, wordsS)
        db.set_words(self.ADDR_INI+self.WORDS_A_OFFSET, wordsA)
            
    def print_mem(self,db):
        from datetime import datetime
        # somente primeiros 16 bits
        digS = db.get_words(self.ADDR_INI+self.BITS_S_OFFSET)[0]
        digA = db.get_words(self.ADDR_INI+self.BITS_A_OFFSET)[0]
        changed = [False]*64
            
        # first 'n' words
        print(fg.WHITE+"{:%H:%M:%S}    ".format(datetime.now()),"%4d "*(16)%tuple(list(range(0,16)))+("%1x"*(16)%(tuple(range(15,-1,-1)))).upper())
        wS = db.get_words(self.ADDR_INI+self.WORDS_S_OFFSET,16) 
        dS = list("{:016b}".format(digS))
        wA = db.get_words(self.ADDR_INI+self.WORDS_A_OFFSET,16)   
        dA = list("{:016b}".format(digA))
        if self.print_mem_state:
            changed = [x!=y for x,y in zip(self.print_mem_state,wS+dS+wA+dA) ]    
            
        print(fg.WHITE+"{:%H:%M:%S} R/O".format(datetime.now()),end=' ')
        cor = [ fg.RESET if x else fg.WHITE for x in changed[:16] ]
        for x,c in zip(wS,cor):
            print(c+'%04d'%x,end=' ')
        cor = [ fg.RESET if x else fg.WHITE for x in changed[16:32] ]
        for x,c in zip(dS,cor):
            print(c+'%s'%x,end='')
        print('')
        print(fg.WHITE+"{:%H:%M:%S} R/W".format(datetime.now()),end=' ')
        cor = [ fg.RESET if x else fg.WHITE for x in changed[32:48] ]
        for x,c in zip(wA,cor):
            print(c+'%04d'%x,end=' ')
        cor = [ fg.RESET if x else fg.WHITE for x in changed[48:] ]
        for x,c in zip(dA,cor):
            print(c+'%s'%x,end='')
        print(st.RESET_ALL)
        self.print_mem_state = wS+dS+wA+dA 

    def save_log(self,log_file,db,elapsed_time):
        try: 
            with open(log_file,'a') as csv_file:
                csv_writer = csv.writer(csv_file, delimiter=',')
                digS = db.get_words(self.ADDR_INI+self.BITS_S_OFFSET)
                digA = db.get_words(self.ADDR_INI+self.BITS_A_OFFSET)
                strdigS = ("{:016b} "*(len(digS)//16)).strip().format(digS)
                strdigA = ("{:016b} "*(len(digA)//16)).strip().format(digA)
                w = db.get_words(self.ADDR_INI+self.WORDS_S_OFFSET,self.WORDS_MAX_LEN*2)
                strword = ("%04d "*len(w)).strip()%tuple(w)
                row=("{:%H:%M:%S}".format(datetime.now()),"%5d"%int(elapsed_time),strword,strdigS,strdigA)
                csv_writer.writerow(row)
        except:
            raise Exception('*** MEM.save_log: Unable to append log:',log_file)

if __name__ == '__main__':

    clear_screen()

    from pyModbusTCP.server import DataBank as db
    from PLANTsim_PLANT import Plant
    plant = Plant()
    plant.load("PLANTsim_LARI_1.plant")
    memory = Memory()
    memory.init(db,plant)    
    memory.print_mem(db)
    

