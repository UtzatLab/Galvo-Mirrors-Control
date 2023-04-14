# -*- coding: utf-8 -*-
"""
Created on Tue Mar 14 13:34:08 2023

@author: alexm
"""

from labjack import ljm
import numpy as np
from time import sleep 
from time import perf_counter_ns


class Galvos: 
    
    def __init__(self): 
        """
        Constructs scan object with default scan settings. 

        Returns
        -------
        None.

        """
        self.SCALING = 1 # V/degree. Can be set to 0.5, 0.8, or 1. See GVS012 manual

        self.f1 = 100 # mm
        self.f2 = 125 # mm 
        self.ttm = 93.4 # mm, distance from tube lens to mirror over sample holder
        self.mts = 71.6 # mm, distance from mirror to sample
        self.wd = 1 # mm, working distance
        self.BO = 1.7 # mm, thickness of back objective 
        self.dtr = np.pi/180 # conversion from degrees to radians
        
        self.DAC_RANGE = [-10,10] # Voltage range of the DAC
        self.DAC_BITS = 14 # Resolution of DAC voltage range in bits
        self.VOLTAGE_SPACING = (self.DAC_RANGE[1]-self.DAC_RANGE[0])/(2**self.DAC_BITS-1)
        
        self.GalvoX = 0 
        self.GalvoY = 0
        
        self.wx_um, self.wy_um, self.spacing = 50, 50, 10 # Default Scan Parameters if not otherwise set
        self.start_up_time = 2 # s
        
        self.writing_V = 1 # When using I/O register, use 0/1. When using AO register, use voltage. 
        self.LJ_signal_port = "FIO2"
        
        self.x_port = "TDAC0"
        self.y_port = "TDAC1"
        
        
    def V_to_dist(self, V):
        """
        Calculation to determine the distance from the center a given voltage 
        will move.

        Parameters
        ----------
        V : Float
            Input voltage.

        Returns
        -------
        distum : Float
            Output distance in micrometers.

        """
        a = 2*V*(self.f1/self.f2)/self.SCALING
        c = 45-a
        x2 = self.ttm * np.sin(a*self.dtr) / np.sin(c*self.dtr)
        phi = np.arcsin(x2/(np.sqrt(2)*(self.mts-x2/np.sqrt(2))))
        distmm = (self.wd+self.BO) * np.tan(phi)
        distum = distmm * 1000
        return distum


    def dist_to_V(self, um): 
        """
        Calculation to determine the voltage required to move a given distance 
        from the center.

        Parameters
        ----------
        um : Float.
            Input distance in micrometers.

        Returns
        -------
        V : Float
            Output voltage.

        """
        mm = um / 1000
        phi = np.arctan(mm/(self.wd+self.BO))
        x2 = np.sqrt(2)*self.mts / (1 + np.sin(phi)**-1)
        ar = np.arctan(1/(1+(np.sqrt(2)*self.ttm/x2)))
        a = ar / self.dtr
        V = self.SCALING * a * self.f2 / (2 * self.f1)
        return V
    
    
    def _update(self): 
        """
        Function called to write voltage to the Labjack and move the mirrors.
        Auxillary method primarily meant to be called by other methods. 

        Returns
        -------
        None.

        """
        if self.GalvoX > self.DAC_RANGE[0] and self.GalvoX < self.DAC_RANGE[1] and self.GalvoY > self.DAC_RANGE[0] and self.GalvoY < self.DAC_RANGE[1]:
            ljm.eWriteName(self.handle, self.x_port, self.GalvoX)
            ljm.eWriteName(self.handle, self.y_port, self.GalvoY)
            
            
    def set_scan_size(self, wx_um = 50, wy_um = 50, spacing = 10): 
        """
        Sets scan parameters if different from default. The parameters can be 
        entered unlabeled if all three are being changed, or a single parameter 
        can be changed by labeling it.

        Parameters
        ----------
        wx_um : Float, optional
            Distance in micrometers to scan in the x-direction. The default is 50.
        wy_um : TYPE, optional
            Distance in micrometers to scan in the y-direction. The default is 50.
        spacing : Integer, optional
            The mirrors will move every {spacing} steps of the smallest possible 
            movement. Setting to 0 or 1 will have the mirrors move with the 
            smallest steps possible. The default is 10.

        Returns
        -------
        None.

        """
        self.wx_um, self.wy_um, self.spacing = wx_um, wy_um, spacing
        
        self.Vx_range = self.dist_to_V(wx_um/2)
        self.Vy_range = self.dist_to_V(wy_um/2)
        
        if spacing == 0: 
            print("Divide by 0 error. Set spacing to 1.")
            spacing = 1
            
        self.nx = int((2*self.Vx_range)/(self.VOLTAGE_SPACING*spacing))
        self.ny = int((2*self.Vy_range)/(self.VOLTAGE_SPACING*spacing))
        
        
    def run(self, int_time_us = 100, square_raster = False, check_edge = False): 
        """
        Method called to start a full scan of the mirrors.

        Parameters
        ----------
        int_time_us : Float, optional
            Integration time at each position in microseconds. The default is 100.
        square_raster : True or False, optional
            Toggle sawtooth or square raster. The default is False (sawtooth raster).
        check_edge : True or False, optional
            Toggles an additional delay at the first point of each leg of the 
            raster scan. This is used to check that the raster scan is not 
            skipping points--if functioning correctly, a brighter line should 
            appear straight down the left edge of the plotted values. The default
            is False. 

        Returns
        -------
        None.

        """
        edge_mult = 1
        flip_power = 0
        if square_raster: 
            flip_power = 1
        if check_edge: 
            edge_mult = 100
            
        self.set_scan_size(self.wx_um, self.wy_um, self.spacing)
        self.handle = ljm.openS("T7", "USB", "ANY")
        
        sleep(self.start_up_time)
        
        for y in range(self.ny): 
            self.GalvoY = y*self.VOLTAGE_SPACING*self.spacing - self.Vy_range
            if y%2 == 0: 
                flip = 1
            if y%2 == 1: 
                flip = (-1)**flip_power
            for x in range(self.nx): 
                self.GalvoX = (x*self.VOLTAGE_SPACING*self.spacing - self.Vx_range) * flip
                self._update()
                ljm.eWriteName(self.handle, self.LJ_signal_port, self.writing_V)
                if x == 0: 
                    self.sleep_us(int_time_us*edge_mult)
                else: 
                    self.sleep_us(int_time_us)
                ljm.eWriteName(self.handle, self.LJ_signal_port, 0)
                         
                
        self.GalvoX = 0 
        self.GalvoY = 0 
        self._update()
        ljm.close(self.handle)
                
    
    def sleep_us(self, microseconds):
        """
        Sleep function with microsecond resolution.

        Parameters
        ----------
        microseconds : Float
            Time in microseconds to sleep.

        Returns
        -------
        None.

        """
        start_time = perf_counter_ns()
        while True:
            elapsed_time = perf_counter_ns() - start_time
            remaining_time = microseconds - elapsed_time /1000
            if remaining_time <= 0:
                break
    
    def reset(self): 
        """
        Resets the galvos and closes the DAQ. Used to relinquish control of 
        the Labjack if the console crashes.

        Returns
        -------
        None.

        """
        self.GalvoX, self.GalvoY = 0, 0
        self._update()
        ljm.close(self.handle)
        


