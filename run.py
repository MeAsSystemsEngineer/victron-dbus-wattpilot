# by André Rudolph 
#
# testing equipment:
# Multiplus-II 48/3000/35-32
# Raspberry 4 as GX device with firmware 3.31
# CANable-MKS CAN interface
# CG EM540 Smart Meter
# 4 x US2000C Pylontech Batteries
# Fronius Wattpilot 11 J using code by https://github.com/joscha82/wattpilot with firmware 40.7
# __init__.py has to be replaced before built because fsp functions were added
# 
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import wattpilot
import os
import argparse
import time
import sys
import dbus

from dbus.mainloop.glib import DBusGMainLoop
from datetime import datetime

############################
### our own victron packages
############################
sys.path.insert(1, os.path.join(os.path.dirname(__file__), '../'))
from vedbus import VeDbusItemImport

#####################################
### user defined variables start here
#####################################

### logging options
### default output is /dev/console
# status = 0 | 1 - regular status: enabled by default
status = 1
# debug = 0 | 1 - regular debug: disabled by default
debug = 0
# debugRV = 0 | 1 - return values: disabled by default
debugRV = 0

### seconds between two wattpilot requests
### low values may generate high load
WaitInterval = 3

### battery power input/charge settings
### adjust if system can charge 50 ampere or more
MaxChargeCurrent = 35

### battery power output/discharge settings on wattpilot modes
MaxDischargePowerWhenCarPlugged_eco = "1380.0"
MaxDischargePowerWhenCarPlugged_nexttrip = "2180.0"

### AC load settings in ampere on wattpilot modes
MaxChargeAMPsWhenCarPlugged_eco = 16
MaxChargeAMPsWhenCarPlugged_nexttrip = 8
MaxChargeAMPsWhenCarPlugged = 16

###########################################
### PID handler
### used as source for killscript/wattpilot
###########################################
###########################################
with open('/data/script/wattpilot.pid', 'w', encoding='utf-8') as f:
    f.write(str(os.getpid()))

##############
### CLI parser 
##############
parser = argparse.ArgumentParser()
parser.add_argument("ip", help = "IP of wattpilot Device")
parser.add_argument("password", help = "Password of wattpilot")

args = parser.parse_args()

ip = args.ip
password = args.password

####################
### initialize dbus 
####################
DBusGMainLoop(set_as_default=True)

# Connect to the sessionbus. Note that on ccgx we use systembus instead.
dbusConn = dbus.SessionBus() if 'DBUS_SESSION_BUS_ADDRESS' in os.environ else dbus.SystemBus()

# empty dictionary containing the different items
dbusObjects = {}

# check if the vbus.ttyO1 exists (it normally does on a ccgx, and for linux a pc, there is
# some emulator.
hasVEBus = 'com.victronenergy.vebus.ttyO1' in dbusConn.list_names()

################################
### dbus examples using OS calls
### use dbus-spy as alternative
################################

### read - better use python libraries
# stream = os.popen('/usr/bin/dbus -y com.victronenergy.settings /Settings/CGwacs/MaxDischargePower GetValue')
# output = stream.read()
# ### make sure there are no newlines within output
# str_MaxDischargePower = output.strip()

###  write better use python libraries
# stream = os.popen('/usr/bin/dbus -y com.victronenergy.settings /Settings/CGwacs/MaxDischargePower SetValue %-1')
# output = stream.read() 

########################
### defaulting functions
########################

def defaultMaxChargeCurrent():

    ### get /Settings/SystemSetup/MaxChargeCurrent from Venus OS device
    dbusObjects['int_Settings_SystemSetup_MaxChargeCurrent'] = VeDbusItemImport(dbusConn, 'com.victronenergy.settings', '/Settings/SystemSetup/MaxChargeCurrent')
    if hasVEBus: dbusObjects['int_Settings_SystemSetup_MaxChargeCurrent'] = VeDbusItemImport(dbusConn, 'com.victronenergy.vebus.ttyO1', '/Settings/SystemSetup/MaxChargeCurrent')
    MaxChargeCurrent = dbusObjects['int_Settings_SystemSetup_MaxChargeCurrent'].get_value()
            
    if(debug):
        now = datetime.now()
        print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [Debug] Value of /Settings/SystemSetup/MaxChargeCurrent is: " + str(MaxChargeCurrent))
        
    if(MaxChargeCurrent != -1.0):
        if(status):
            now = datetime.now()
            print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [Status] Set charger power to maximum (-1.0)")
        
        output = dbusObjects['int_Settings_SystemSetup_MaxChargeCurrent'].set_value(-1)
        
        if(debugRV):
            now = datetime.now()
            print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [Debug Return Value] Function defaultMaxChargeCurrent() command returned: " + str(output))
            
    ### MaxChargeCurrent is already disabled
    else:
        if(debug):
            now = datetime.now()
            print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [Debug] Nothing to do as /Settings/SystemSetup/MaxChargeCurrent is already disabled")

def defaultMaxDischargePower():

    ### get /Settings/CGwacs/MaxDischargePower from Venus OS device
    dbusObjects['float_Settings_CGwacs_MaxDischargePower'] = VeDbusItemImport(dbusConn, 'com.victronenergy.settings', '/Settings/CGwacs/MaxDischargePower')
    if hasVEBus: dbusObjects['float_Settings_CGwacs_MaxDischargePower'] = VeDbusItemImport(dbusConn, 'com.victronenergy.vebus.ttyO1', '/Settings/CGwacs/MaxDischargePower')
    MaxDischargePower = dbusObjects['float_Settings_CGwacs_MaxDischargePower'].get_value()
            
    if(debug):
        now = datetime.now()
        print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [Debug] Value of /Settings/CGwacs/MaxDischargePower is: " + str(MaxDischargePower))
        
    if(MaxDischargePower != -1.0):
        if(status):
            now = datetime.now()
            print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [Status] Set inverter power to maximum (-1.0)")
        
        output = dbusObjects['float_Settings_CGwacs_MaxDischargePower'].set_value(-1)
        
        if(debugRV):
            now = datetime.now()
            print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [Debug Return Value] Function defaultMaxDischargePower() command returned: " + str(output))
            
    ### MaxDischargePower is already disabled
    else:
        if(debug):
            now = datetime.now()
            print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [Debug] Nothing to do as /Settings/CGwacs/MaxDischargePower is already disabled")

def defaultAcPowerSetPoint():

    ### get GridPoint from Venus OS device
    dbusObjects['float_Settings_CGwacs_AcPowerSetPoint'] = VeDbusItemImport(dbusConn, 'com.victronenergy.settings', '/Settings/CGwacs/AcPowerSetPoint')
    if hasVEBus: dbusObjects['float_Settings_CGwacs_AcPowerSetPoint'] = VeDbusItemImport(dbusConn, 'com.victronenergy.vebus.ttyO1', '/Settings/CGwacs/AcPowerSetPoint')
    AcPowerSetPoint = dbusObjects['float_Settings_CGwacs_AcPowerSetPoint'].get_value()
    
    if(debug):
        now = datetime.now()
        print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [Debug] Value of /Settings/CGwacs/AcPowerSetPoint (GridPoint) is: " + str(AcPowerSetPoint))
        
    if(AcPowerSetPoint != float(0)):
        if(status):
            now = datetime.now()
            print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [Status] Set grid point to 0.0 watts ")
        
        output = dbusObjects['float_Settings_CGwacs_AcPowerSetPoint'].set_value(0.0)
        
        if(debugRV):
            now = datetime.now()
            print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [Debug Return Value] Function defaultAcPowerSetPoint() command returned: " + str(output))
    
    ### Grid Point is already at 0.0
    else:
        if(debug):
            now = datetime.now()
            print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [Debug] Nothing to do as /Settings/CGwacs/AcPowerSetPoint is already at 0.0")

def setDynamicMaxChargeCurrent():

    ### get Soc from Venus OS device
    dbusObjects['int_Soc'] = VeDbusItemImport(dbusConn, 'com.victronenergy.battery.socketcan_can0', '/Soc')
    if hasVEBus: dbusObjects['int_Soc'] = VeDbusItemImport(dbusConn, 'com.victronenergy.battery.socketcan_can0', '/Soc')
    Soc = dbusObjects['int_Soc'].get_value()
            
    if(debug):
        now = datetime.now()
        print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [Debug] Value of /Soc is: " + str(Soc))
        
    ### get /Settings/SystemSetup/MaxChargeCurrent from Venus OS device
    dbusObjects['int_Settings_SystemSetup_MaxChargeCurrent'] = VeDbusItemImport(dbusConn, 'com.victronenergy.settings', '/Settings/SystemSetup/MaxChargeCurrent')
    if hasVEBus: dbusObjects['int_Settings_SystemSetup_MaxChargeCurrent'] = VeDbusItemImport(dbusConn, 'com.victronenergy.vebus.ttyO1', '/Settings/SystemSetup/MaxChargeCurrent')
    MaxChargeCurrent = dbusObjects['int_Settings_SystemSetup_MaxChargeCurrent'].get_value()
            
    if(debug):
        now = datetime.now()
        print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [Debug] Value of /Settings/SystemSetup/MaxChargeCurrent is: " + str(MaxChargeCurrent))
        
    RoundedSoC = round (Soc, -1)
    DynamicChargeCurrent = round((101 - RoundedSoC) * MaxChargeCurrent / 100)
            
    if(DynamicChargeCurrent != MaxChargeCurrent):
        if(debug):
            now = datetime.now()
            print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [Debug] Set charger power to " + str(DynamicChargeCurrent) + " ampere")
        
        output = dbusObjects['int_Settings_SystemSetup_MaxChargeCurrent'].set_value(DynamicChargeCurrent)
    
    if(debugRV):
        now = datetime.now()
        print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [Debug Return Value] Function setDynamicMaxChargeCurrent() command returned: " + str(output))

###########################
### create wattpilot object
###########################
try:
    solarwatt = wattpilot.Wattpilot(ip,password)
except:
    print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [StateChange] Something went wrong on wattpilot connection")

while not solarwatt.connected:
   
    if(debug):
        now = datetime.now()
        print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [Debug] wattpilot is not yet connected")
        print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [Debug] Starting to connect to wattpilot " + ip )
    
    ####################################################################
    ### default all values if no connection is possible
    ### parameters: MaxDischargePower, AcPowerSetPoint, MaxChargeCurrent
    ####################################################################
    defaultMaxChargeCurrent()
    defaultMaxDischargePower()
    defaultAcPowerSetPoint()
    
    #########################################################
    ### try to connect to wattpilot using the given arguments
    #########################################################
    solarwatt.connect()
    
    ### as long as not connected, increase connection_counter by one
    connection_counter = 0
    while not solarwatt.connected:
        connection_counter += 1
        time.sleep(WaitInterval)
        
    ### finally we were able to connect 
    if(status):
        now = datetime.now()
        print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [Status] wattpilot " + ip + " connected:" + str(solarwatt.connected) + " after " + str(connection_counter * WaitInterval) + " seconds" )
        ### give one more second for the wattpilot to get ready
        time.sleep(1)
        
    ### wattpilot is now connected
    while solarwatt.connected:
        if(debug):
            now = datetime.now()
            print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [Debug] Status of wattpilot is:")
            print(solarwatt)
            print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [Debug] wattpilot has " + str(solarwatt.power) + "kW load.")
            print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [Debug] ForceSinglePhase is " + str(solarwatt.fsp))
            
        ### possible wattpilot return values
        ### see /data/wattpilot-main/wattpilot-main/src/wattpilot/__init__.py
        ### status: "no car" | "charging" | "ready" | "complete"
        ### mode: "Default" | "Eco" | "Next Trip"
         
        ##############################################################################
        # state is "no car": disable inverter power limits and set grid point to zero
        ##############################################################################
        if(( str(solarwatt.carConnected) == "no car" )):
            defaultMaxChargeCurrent()
            defaultMaxDischargePower()
            defaultAcPowerSetPoint()
            
            if(debug):
                now = datetime.now()
                print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [Debug] State is no car: disable inverter power limits and set grid point to zero.")
            
            #############################################################################################
            ### change power and phase usage ONLY if status is "no car" so running charge is not impacted
            ### case: mode is Eco
            ##############################################################################################
            if( str(solarwatt.mode) == "Eco" ):
                
                if( solarwatt.fsp ):
                    now = datetime.now()
                    print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [StateChange] Unset ForceSinglePhase.")
                    # phaseSwitchMode (Auto=0, Force_1=1, Force_3=2)
                    # workaround: Force_3 setting is needed to change value of fsp to false
                    solarwatt.send_update("psm", 2)
                    time.sleep(1)
                    # now we can set back to Auto
                    solarwatt.send_update("psm", 0)
                
                if(solarwatt.amp != MaxChargeAMPsWhenCarPlugged_eco):
                    now = datetime.now()
                    print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [StateChange] Set Power to " + str(MaxChargeAMPsWhenCarPlugged_eco) + " A.")
                    solarwatt.set_power(MaxChargeAMPsWhenCarPlugged_eco)
            
            #############################################################################################
            ### change power and phase usage ONLY if status is "no car" so running charge is not impacted
            ### case: mode is Next Trip
            #############################################################################################
            elif( str(solarwatt.mode) == "Next Trip" ):
                
                if( not solarwatt.fsp ):
                    now = datetime.now()
                    print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [StateChange] Set ForceSinglePhase.")
                    # phaseSwitchMode (Auto=0, Force_1=1, Force_3=2)
                    solarwatt.send_update("psm", 1)
                
                if(solarwatt.amp != MaxChargeAMPsWhenCarPlugged_nexttrip):
                    now = datetime.now()
                    print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [StateChange] Set Power to " + str(MaxChargeAMPsWhenCarPlugged_nexttrip) + " A.")
                    solarwatt.set_power(MaxChargeAMPsWhenCarPlugged_nexttrip)
            
            #############################################################################################
            ### change power and phase usage ONLY if status is "no car" so running charge is not impacted
            ### case: mode is Default
            #############################################################################################
            elif( str(solarwatt.mode) == "Default" ):
                
                if( solarwatt.fsp ):
                    now = datetime.now()
                    print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [StateChange] Unset ForceSinglePhase.")
                    # phaseSwitchMode (Auto=0, Force_1=1, Force_3=2)
                    # workaround: Force_3 setting is needed to change value of fsp to false
                    solarwatt.send_update("psm", 2)
                    time.sleep(1)
                    # now we can set back to Auto
                    solarwatt.send_update("psm", 0)
                
                if(solarwatt.amp != MaxChargeAMPsWhenCarPlugged):
                    now = datetime.now()
                    print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [StateChange] Set Power to " + str(MaxChargeAMPsWhenCarPlugged) + " A.")
                    solarwatt.set_power(MaxChargeAMPsWhenCarPlugged)
        
        ######################################################################
        # state is "charging": adjust inverter power limits and set grid point
        ######################################################################
        elif(( str(solarwatt.carConnected) == "charging" )):
            
            ######################################################################################################
            ### limit inverter power to value stored within MaxDischargePowerWhenCarPlugged_eco when mode is "Eco"
            ######################################################################################################
            if( str(solarwatt.mode) == "Eco" ):
                if(debug):
                    now = datetime.now()
                    print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [Debug] Car is " + str(solarwatt.carConnected) + ". Mode is " + str(solarwatt.mode))
                    print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [Debug] ForceSinglePhase is " + str(solarwatt.fsp) + " and Power is set to " + str(solarwatt.amp) + " A per phase")
                    
                defaultAcPowerSetPoint()
                setDynamicMaxChargeCurrent()
                          
                ### get MaxDischargePower from Venus OS device
                dbusObjects['float_Settings_CGwacs_MaxDischargePower'] = VeDbusItemImport(dbusConn, 'com.victronenergy.settings', '/Settings/CGwacs/MaxDischargePower')
                if hasVEBus: dbusObjects['float_Settings_CGwacs_MaxDischargePower'] = VeDbusItemImport(dbusConn, 'com.victronenergy.vebus.ttyO1', '/Settings/CGwacs/MaxDischargePower')
                MaxDischargePower = str(dbusObjects['float_Settings_CGwacs_MaxDischargePower'].get_value())
                
                if(debug):
                    now = datetime.now()
                    print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [Debug] /Settings/CGwacs/MaxDischargePower is: " + str(MaxDischargePower))
                    
                ### limit inverter power to MaxDischargePowerWhenCarPlugged_eco
                if(MaxDischargePower != MaxDischargePowerWhenCarPlugged_eco):
                    if(status):
                        now = datetime.now()
                        print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [Status] Car plugged and charging. Set Inverter Power to " + str(MaxDischargePowerWhenCarPlugged_eco) + " watts")
                        
                    output = dbusObjects['float_Settings_CGwacs_MaxDischargePower'].set_value(MaxDischargePowerWhenCarPlugged_eco)
                    
                    if(debugRV):
                        now = datetime.now()
                        print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [Debug Return Value] Command returned: " + str(output))
                        
                ### inverter power is already at value of variable MaxDischargePowerWhenCarPlugged_eco
                else:
                    if(debug):
                        now = datetime.now()
                        print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [Debug] Nothing to do. Inverter power is already at value of variable MaxDischargePowerWhenCarPlugged_eco")
            
            #################################################################################################################
            ### limit inverter power to value stored within MaxDischargePowerWhenCarPlugged_nexttrip when mode is "Next Trip"
            #################################################################################################################
            elif( str(solarwatt.mode) == "Next Trip" ):
                if(debug):
                    now = datetime.now()
                    print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [Debug] Car is " + str(solarwatt.carConnected) + ". Mode is " + str(solarwatt.mode))
                    
                defaultAcPowerSetPoint()
                
                ### get MaxDischargePower from Venus OS device
                dbusObjects['float_Settings_CGwacs_MaxDischargePower'] = VeDbusItemImport(dbusConn, 'com.victronenergy.settings', '/Settings/CGwacs/MaxDischargePower')
                if hasVEBus: dbusObjects['float_Settings_CGwacs_MaxDischargePower'] = VeDbusItemImport(dbusConn, 'com.victronenergy.vebus.ttyO1', '/Settings/CGwacs/MaxDischargePower')
                MaxDischargePower = str(dbusObjects['float_Settings_CGwacs_MaxDischargePower'].get_value())
                
                if(debug):
                    now = datetime.now()
                    print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [Debug] /Settings/CGwacs/MaxDischargePower is: " + str(MaxDischargePower))
                
                ### limit inverter power to MaxDischargePowerWhenCarPlugged_nexttrip
                if(MaxDischargePower != MaxDischargePowerWhenCarPlugged_nexttrip):
                    
                    if(status):
                        now = datetime.now()
                        print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [Status] Car plugged and charging. Set Inverter Power to " + str(MaxDischargePowerWhenCarPlugged_nexttrip) + " watts")
                        
                    output = dbusObjects['float_Settings_CGwacs_MaxDischargePower'].set_value(MaxDischargePowerWhenCarPlugged_nexttrip)                
                    
                    if(debugRV):
                        now = datetime.now()
                        print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [Debug Return Value] Command returned: " + str(output))
                        
                ### inverter power is already at value of variable MaxDischargePowerWhenCarPlugged_nexttrip
                else:
                    if(debug):
                        print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [Debug] Nothing to do. Inverter power is already at value of variable MaxDischargePowerWhenCarPlugged_nexttrip")
            
            ############################################################################################################
            ### set gridpoint to solarwatt.power when mode is "Default" - no power is used from battery for car changing
            ############################################################################################################
            elif( str(solarwatt.mode) == "Default" ):
                if(debug):
                    now = datetime.now()
                    print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [Debug] Car is " + str(solarwatt.carConnected) + ". Mode is " + str(solarwatt.mode))
                    
                defaultMaxDischargePower()
                
                ### get GridPoint from Venus OS device
                dbusObjects['float_Settings_CGwacs_AcPowerSetPoint'] = VeDbusItemImport(dbusConn, 'com.victronenergy.settings', '/Settings/CGwacs/AcPowerSetPoint')
                if hasVEBus: dbusObjects['float_Settings_CGwacs_AcPowerSetPoint'] = VeDbusItemImport(dbusConn, 'com.victronenergy.vebus.ttyO1', '/Settings/CGwacs/AcPowerSetPoint')
                AcPowerSetPoint = dbusObjects['float_Settings_CGwacs_AcPowerSetPoint'].get_value()
                
                if(debug):
                    now = datetime.now()
                    print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [Debug] /Settings/CGwacs/AcPowerSetPoint (GridPoint) is: " + str(AcPowerSetPoint))
                
                ### set GridPoint to AcPowerSetPoint
                if(AcPowerSetPoint != (float(solarwatt.power) * 1000)):
                    
                    if(status):
                        now = datetime.now()
                        print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [Status] Wattpilot has " + str((float(solarwatt.power) * 1000)) + " watts load")
                        print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [Status] Grid Point is: " + str(AcPowerSetPoint))
                        print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [Status] Car plugged and charging. Set Grid Point to " + str((float(solarwatt.power) * 1000)) + " watts")
                         
                    output = dbusObjects['float_Settings_CGwacs_AcPowerSetPoint'].set_value((float(solarwatt.power) * 1000))  
                    
                    if(debugRV):
                        now = datetime.now()
                        print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [Debug Return Value] Command returned: " + str(output))
                        
                ### inverter power is already at value of variable of AcPowerSetPoint
                else:
                    if(debug):
                        now = datetime.now()
                        print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [Debug] Inverter power is already at value of variable of AcPowerSetPoint. Nothing to do.")
        
        ##########################################################################################
        # state is "ready" or "complete": disable inverter power limits and set grid point to zero
        ##########################################################################################
        else:
            
            defaultMaxChargeCurrent()
            defaultMaxDischargePower()
            defaultAcPowerSetPoint()

        # wait defined time before checking car state again
        time.sleep(WaitInterval)
    
    ### wattpilot is no more connected. Free up resources and wait one minute to reconnect.
    if(status):
        now = datetime.now()
        print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [Status] wattpilot at " + ip + " has the following state: " + str(solarwatt.connected))
        print("[" + str(now.strftime("%Y-%m-%d %H:%M:%S")) + "] [Status] trying to reconnect in 60 seconds...")
        #### cleaning up and try to reconnect within the next loop
        solarwatt.disconnect()
        time.sleep(60)
