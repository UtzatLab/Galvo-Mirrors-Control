# -*- coding: utf-8 -*-
"""
Created on Sat Jan  7 10:08:55 2023

@author: alexm

Code to manually control Thorlabs galvo mirrors using a Labjack T7.

"""

import numpy as np
import keyboard as kb
from labjack import ljm

handle = ljm.openS("T7", "USB", "ANY")


# DAC Initialization
LJTick_DAC = 1 # 0 if not present, 1 if present

if LJTick_DAC:
    DAC_RANGE = [-10,10] # Voltage range of the DAC
    DAC_BITS = 14 # Resolution of DAC voltage range in bits
else: 
    DAC_RANGE = [0, 5]
    DAC_BITS = 12

VOLTAGE_LEVELS = np.linspace(DAC_RANGE[0], DAC_RANGE[1], num=2**DAC_BITS, endpoint=True)
VOLTAGE_SPACING = (DAC_RANGE[1]-DAC_RANGE[0])/(2**DAC_BITS-1)


# Galvo Initialization 
SCALING = 1 # V/degree. Can be set to 0.5, 0.8, or 1. See GVS012 manual

f1 = 100 # mm
f2 = 125 # mm 
ttm = 93.4 # mm, distance from tube lens to mirror over sample holder
mts = 71.6 # mm, distance from mirror to sample
wd = 1 # mm, working distance
BO = 1.7 # mm, thickness of back objective 
dtr = np.pi/180 # conversion from degrees to radians


def V_to_dist(V):
    a = 2*V*(f1/f2)/SCALING
    c = 45-a
    x2 = ttm * np.sin(a*dtr) / np.sin(c*dtr)
    phi = np.arcsin(x2/(np.sqrt(2)*(mts-x2/np.sqrt(2))))
    distmm = (wd+BO) * np.tan(phi)
    distum = distmm * 1000
    return distum

def dist_to_V(um): 
    mm = um / 1000
    phi = np.arctan(mm/(wd+BO))
    x2 = np.sqrt(2)*mts / (1 + np.sin(phi)**-1)
    ar = np.arctan(1/(1+(np.sqrt(2)*ttm/x2)))
    a = ar / dtr
    V = SCALING * a * f2 / (2 * f1)
    return V
    

GalvoX = 0
GalvoY = 0


def update(): 
    global GalvoX
    global GalvoY
    if GalvoX > DAC_RANGE[0] and GalvoX < DAC_RANGE[1] and GalvoY > DAC_RANGE[0] and GalvoY < DAC_RANGE[1]:
        # ljm.eWriteName(handle, "TDAC0", GalvoX)
        ljm.eWriteName(handle, "DAC0", GalvoX)
        # ljm.eWriteName(handle, "TDAC1", GalvoY)


def Reset():
    global GalvoX
    global GalvoY
    GalvoX = 0 
    GalvoY = 0
    update()
    

def Show_voltage(): 
    print(f"x: {GalvoX} V; y: {GalvoY} V")

def Show_position():
    distx = V_to_dist(GalvoX)
    disty = V_to_dist(GalvoY)
    print(f"x: {round(distx,4)} um, y: {round(disty,4)} um")
    

saved_locations = {}

def Save_position(name):
    saved_locations.update({str(name) : [GalvoX, GalvoY]})
    
def Load_position(name):
    global GalvoX
    global GalvoY
    GalvoX = saved_locations[str(name)][0]
    GalvoY = saved_locations[str(name)][1]
    update()
    
    
def Set_voltage(x, y): 
    global GalvoX
    global GalvoY
    GalvoX = x
    GalvoY = y
    update()
    
def Set_position(x, y): 
    global GalvoX
    global GalvoY
    dx = dist_to_V(x)
    dy = dist_to_V(y)
    GalvoX = dx
    GalvoY = dy
    

def controls(): 
    print("""
    run() commands: 
        Move using arrow keys 
        
        Increase/decrease corseness with +/-
        Show corseness with c
        
        Show position with p 
        Show voltage with v 
        
        Save position with s. Enter name for save. Case sensitive. 
        Load position with l. Enter name for save. Case sensitive.
        
        Reset position to origin with r 
        
        Exit and return to original position with esp 
        Exit and save position with enter
        
        Press m for more options

    """)



def run(): 
    global GalvoX
    global GalvoY
    xi = GalvoX
    yi = GalvoY
    
    controls()
    
    corse = 4
    while True:
        dV = VOLTAGE_SPACING*10**(corse-1)
        event = kb.read_event()
        
        if event.event_type == kb.KEY_DOWN and event.name == '+':
            if corse < 4:
                corse += 1
            print(f"Corseness: {corse}")

        if event.event_type == kb.KEY_DOWN and event.name == '-':
            if corse > 1:
                corse -= 1
            print(f"Corseness: {corse}")
            
        num = [0,1,2,3,4,5,6,7,8,9]
        for n in num: 
            if event.event_type == kb.KEY_DOWN and event.name == str(n):
                corse = n
                
        if event.event_type == kb.KEY_DOWN and event.name == 'c':
            print(f"Corseness: {corse}")
            
            
        if event.event_type == kb.KEY_DOWN and event.name == 'left':
            if GalvoX > DAC_RANGE[0]+dV:
                GalvoX -= dV
                update()
            else: 
                print("Negavtive x limit reached")
                
        if event.event_type == kb.KEY_DOWN and event.name == 'right':
            if GalvoX < DAC_RANGE[1]-dV:
                GalvoX += dV
                update()
            else: 
                print("Positive x limit reached")
            
        if event.event_type == kb.KEY_DOWN and event.name == 'up':
            if GalvoY < DAC_RANGE[1]-dV:
                GalvoY += dV
                update()
            else: 
                print("Positive y limit reached")
                
        if event.event_type == kb.KEY_DOWN and event.name == 'down':
            if GalvoY > DAC_RANGE[0]+dV:
                GalvoY -= dV
                update()
            else: 
                print("Negavtive y limit reached")
                
            
        if event.event_type == kb.KEY_DOWN and event.name == 'v':
            Show_voltage()
            print(f'AIN0: {2*ljm.eReadName(handle, "AIN0")}')
            print(f'AIN1: {2*ljm.eReadName(handle, "AIN1")}')

        
        if event.event_type == kb.KEY_DOWN and event.name == 'p':
            Show_position()
            
            
        if event.event_type == kb.KEY_DOWN and event.name == 's':
            print("Save name?")
            name = input()
            print(f"Save name: {name} at ({GalvoX}, {GalvoY}) V")
            Save_position(str(name))
        
        if event.event_type == kb.KEY_DOWN and event.name == 'l':
            print("Save name?")
            name = input()
            if name in saved_locations: 
                Load_position(str(name))
                print(f"Opened {name} at ({GalvoX}, {GalvoY}) V")
            else: 
                print(f"{name} invalid save name.")
                
            
        if event.event_type == kb.KEY_DOWN and event.name == 'r':
            Reset()
            print("Position reset to center.")
    
    
        # Exit scroll and return to original position
        if event.event_type == kb.KEY_DOWN and event.name == 'esc':
            print(f"Reset from ({GalvoX},{GalvoY}) V to original ({xi},{yi}) V.")
            Set_voltage(xi, yi)
            ljm.close(handle)
            break
        
        if event.event_type == kb.KEY_DOWN and event.name == 'enter':
            print("Holding current positions: ")
            Show_voltage()
            Show_position()

        if event.event_type == kb.KEY_DOWN and event.name == 'm':
            print("""Select a number and hit enter to confirm: 
                  0: Exit extra options menu.
                  1: Show saved positions.
                  2: Manually set voltage. 
                  3: Manually set position in um.""")
            response = input()
            if response == "0": 
                print("Exited.")
                pass
            if response == "1":
                print(saved_locations)
            if response == "2": 
                print("x Voltage:")
                x = float(input())
                print("y Voltage:")
                y = float(input())
                Set_voltage(x, y)
                print("Voltarge set to:")
                Show_voltage()
            if response == "3": 
                print("x position:")
                x = float(input())
                print("y position:")
                y = float(input())
                Set_position(x, y)
                print("Position set to:")
                Show_position()

   
run()
# Set_voltage(0,0)           
# ljm.close(handle)

#x: 3.126411524140869 V; y: 2.5990355856680707 V
