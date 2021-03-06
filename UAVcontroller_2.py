import logging
import time
import io

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.positioning.motion_commander import MotionCommander
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crazyflie.syncLogger import SyncLogger
from cflib.crazyflie.log import LogConfig, Log, LogVariable
from datetime import datetime
        
class UAVController():

    def __init__(self, targetURI=None):
        """
        Function: __init__
        Purpose: Initialize all necessary UAV functionality
        Inputs: none
        Outputs: none
        """

        cflib.crtp.init_drivers()

        #self.FD = open("logFile.txt", "w")
     
        self.timeout = True
        self.available = []
        self.UAV = Crazyflie()
        self.param = None
        self.airborne = False
        self._recentDataPacket = None
        self._receivingDataPacket = False

        #Attempt to locate UAV by scanning available interface
        for _ in range(0,500):
            if(len(self.available) > 0):
                self.timeout = False
                break #If a UAV is found via scanning, break out of this loop
            else:
                self.available = cflib.crtp.scan_interfaces()            

        if(len(self.available) > 0):
            if(targetURI != None):
                for i in range(len(self.available)):
                    if(self.available[i][0] == targetURI):
                        self.UAV.open_link(self.available[i][0])
                        self.connectedToTargetUAV = True
                    else:
                        self.connectedToTargetUAV = False
            else:
                self.UAV.open_link(self.available[0][0])
            
            while(self.UAV.is_connected() == False): time.sleep(0.1)
            self.MC = MotionCommander(self.UAV)
            #Create desired logging parameters
            self.UAVLogConfig = LogConfig(name = "UAVLog", period_in_ms=100)
            #self.UAVLogConfig.add_variable('pm.batteryLevel', 'float')
            self.UAVLogConfig.add_variable('pm.vbat', 'float')
            self.UAVLogConfig.add_variable('pm.batteryLevel', 'float')
            #self.UAVLogConfig.add_variable('stateEstimate.x', 'float')
            #self.UAVLogConfig.add_variable('stateEstimate.y', 'float')
            self.UAVLogConfig.add_variable('stateEstimate.z', 'float')
            self.UAVLogConfig.add_variable('pm.chargeCurrent', 'float')
            self.UAVLogConfig.add_variable('pm.extCurr', 'float')
            self.UAVLogConfig.add_variable('pwm.m1_pwm', 'float')
            #self.UAVLogConfig.add_variable('baro.pressure', 'float')
            #self.UAVLogConfig.add_variable('extrx.thrust', 'float')
            #Add more variables here for logging as desired

            self.UAV.log.add_config(self.UAVLogConfig)
            if(self.UAVLogConfig.valid):
                self.UAVLogConfig.data_received_cb.add_callback(self._getUAVDataPacket)
                self.UAVLogConfig.start()
            else:
                logger.warning("Could not setup log configuration")

        self._startTime = time.time() #For testing purposes
        self._trialRun = 0
        #End of function

    def done(self):
        """
        Function: done
        Purpose: Close connection to UAV to terminate all threads running
        Inputs: none
        Outputs: none
        """
        self.UAVLogConfig.stop()
        self.UAV.close_link()
        self.airborne = False
        return
        
    def launch(self):
        """
        Function: launch
        Purpose: Instruct the UAV to takeoff from current position to the default height
        Inputs: none
        Outputs: none
        """
        self.airborne = True
        self.MC.take_off()
        #End of function
        return

    def land(self):
        """
        Function: launch
        Purpose: Instruct the UAV to land on the ground at current position
        Inputs: none
        Outputs: none
        """
        self.MC.land()
        return
    
    def move(self, distanceX, distanceY, distanceZ, velocity):
        """
        Function: move
        Purpose: A wrapper function to instruct an UAV to move <x, y, z> distance from current point
        Inputs: distance - a floating point value distance in meters
                velocity - a floating point value velocity in meters per second
        Outputs: none
        """
        if(self.airborne == False):
            self.launch()

        self.MC.move_distance(distanceX, distanceY, distanceZ, velocity)
        #End of function
        return

    def rotate(self, degree):
        """
        Function: rotate
        Purpose: A wrapper function to instruct an UAV to rotate
        Inputs: degree - a floating point value in degrees
        Outputs: none
        """
        
        if(self.airborne == False):
            self.launch()
        
        if(degree < 0):
            print("UC: rotate - Going Right")
            locDeg = 0
            #self.MC.turn_right(abs(degree))
            for _ in range(1,int(abs(degree)/1)):
                locDeg += 1
                self.MC.turn_right(1)
            self.MC.turn_right(abs(degree)-locDeg)
        else:
            print("UC: rotate - Going Left")
            self.MC.turn_left(abs(degree))

        #Delay by 1 seclond, to allow for total rotation time
        time.sleep(1)
        return
        
    def getBatteryLevel(self):
        """
        Function: getBatteryLevel
        Purpose: A function that reads the UAV battery level from a IOStream
        Inputs: none
        Outputs: none
        Description: 
        """
        retVal = None
        if(self._recentDataPacket != None and self._receivingDataPacket == False):
            retVal = self._recentDataPacket["pm.vbat"]      
            
        return retVal

    def getHeight(self):
        """
        Function: getCurrentHeight
        Purpose: A function that reads the UAV height from a IOStream
        Inputs: none
        Outputs: none
        Description: 
        """
        retVal = None
        if(self._recentDataPacket != None and self._receivingDataPacket == False):
            retVal = self._recentDataPacket["stateEstimate.z"]

        return retVal

    def isCharging(self):
        """
        Function: getCurrentHeight
        Purpose: A function that reads the UAV height from a IOStream
        Inputs: none
        Outputs: none
        Description: 
        """
        retVal = None
        if(self._recentDataPacket != None and self._receivingDataPacket == False):
            retVal = self._recentDataPacket["pm.chargeCurrent"]

        return retVal
        
    def _getUAVDataPacket(self, ident, data, logconfig):
        """
        Function: getUAVDataPacket
        Purpose: Process a data packet received from the UAV
        Inputs: ident -
                data -
                logconfig -
        Outputs: None
        Description: A user should never call this function.
        """
        self._receivingDataPacket = True
        self._recentDataPacket = data
        self._receivingDataPacket = False 

    def appendToLogFile(self):
        """
        Function: appendToLogFile
        Purpose: append log variables to log file 'log.txt.'
        Inputs: none
        Outputs: none
        Description: 
        """
        #retVal = None
        if(self._recentDataPacket != None and self._receivingDataPacket == False):
            current = self._recentDataPacket["pm.chargeCurrent"]
            extcurrent = self._recentDataPacket["pm.extCurr"]
            voltage = self._recentDataPacket["pm.vbat"]
            bat_level = self._recentDataPacket["pm.batteryLevel"]
            height = self._recentDataPacket["stateEstimate.z"]
            #x = self._recentDataPacket["stateEstimate.y"]
            #y = self._recentDataPacket["stateEstimate.x"]
            m1_pwm = self._recentDataPacket["pwm.m1_pwm"]
            #extrx_thrust = self._recentDataPacket["extrx.thrust"]
            #baro_pressure = self._recentDataPacket["baro.pressure"]


        with open('log2.txt', 'a') as file:
            #print(batlevel)            
            file.write(str(datetime.now()) + '\n')
            file.write('bat_voltage: ' + str(voltage) + '\n')
            file.write('bat_level: ' + str(bat_level) + '\n')
            file.write('crg_current: ' + str(current) + '\n')
            file.write('ext_current: ' + str(extcurrent) + '\n')
            file.write('height: ' + str(height) + '\n')
            #file.write('x: ' + str(x) + '\n')
            #file.write('y: ' + str(y) + '\n')
            file.write('m1_pwm: ' + str(m1_pwm) + '\n')
            #file.write('extrx_thrust: ' + str(extrx_thrust) + '\n')
            #file.write('baro_pressure: ' + str(baro_pressure) + '\n')

        #return retVal
