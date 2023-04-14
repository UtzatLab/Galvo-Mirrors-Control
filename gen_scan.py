# -*- coding: utf-8 -*-
"""
Created on Tue Mar 14 13:30:00 2023

@author: alexm
"""
import numpy as np
import multiprocessing as mp

import matplotlib.pyplot as plt

import TimeTagger as tt 
import Galvos_scan as gs



APD_ch = 1
DAC_ch = 5 
laser_ch = 3

int_time = 0.01
int_time_us = int_time * 10**6
int_time_ps = int_time * 10**12

g = gs.Galvos()

if __name__ == '__main__':
    
    square_raster = False
    
    g.set_scan_size(7, 7, 1)
    
    nx_pix = g.nx
    ny_pix = g.ny
    
    n_pixels = nx_pix*ny_pix
    
    tagger = tt.createTimeTagger()
    
    delay_signal = tt.DelayedChannel(tagger, DAC_ch, int_time_ps)
    delay_ch = delay_signal.getChannel()
    #tagger.setDeadtime(DAC_ch, 10002000) # Max dead time 393200000
    tagger.setTriggerLevel(DAC_ch, 0.169)
    
    cbm = tt.CountBetweenMarkers(tagger, 1, DAC_ch, -DAC_ch, n_pixels)
    p1 = mp.Process(target = g.run, args = (int_time_us, square_raster, True))
    p1.start()
    
    img = np.zeros((ny_pix, nx_pix))
    
    while p1.is_alive():
        counts = cbm.getData()
        
        img = np.reshape(counts, (ny_pix, nx_pix))
        '''
        for i in range(ny_pix):
            if i%2 == 1:
                img[i,:] = img[i,::-1]
        '''
        # plt.imshow(img)
        
        fig, ax = plt.subplots(1, 1, figsize=(13,10))
        ax.set_aspect('equal')
        ax.tick_params(axis="both", labelsize = 18)
        img = ax.imshow(img,cmap='viridis', interpolation='None', extent = [-g.Vx_range, g.Vx_range, -g.Vy_range, g.Vy_range])
        cbar = plt.colorbar(img)
        cbar.ax.tick_params(labelsize=18)
        cbar.set_label(label=f'count per {int_time} s',size=24)

        plt.xlabel(r"$x (V)$", size = 24)
        plt.ylabel(r"$y (V)$", size = 24)
        
                
        plt.pause(.0001)
    #plt.show()
    tt.freeTimeTagger(tagger)
    
    
