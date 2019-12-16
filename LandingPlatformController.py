#!/bin/env python3

import logging
import time
import cflib.crtp
import random

from cflib.crazyflie import Crazyflie
from cflib.utils.callbacks import Caller
from cflib.positioning.motion_commander import MotionCommander
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie

cflib.crtp.init_drivers()
available = cflib.crtp.scan_interfaces()
for i in available:
    print("Interface with URI [%s] found and name/comment [%s]" % (i[0], i[1]))

crazyflie = Crazyflie()
#crazyflie.connected.add_callback(crazyflie_connected)
if(len(available) > 0):

    with SyncCrazyflie(available[0][0]) as scf:
        with MotionCommander(scf) as UAV:
            UAV.up(1, 0.2)
            time.sleep(1)
            UAV.down(1, 0.2)
    
    
else:
    print("ERROR: Unable to find anything")



