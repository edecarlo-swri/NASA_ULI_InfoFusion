# NATS sample
#
# Optimal Synthesis Inc.
#
# Oliver Chen
# 10.01.2019
#
# Demo of Conflict Detection and Resolution during trajectory simulation
#
# This program run simulation twice to generate two different trajectory results -- without-CDNR and with-CDNR.  Finally, users can compare the difference between them.

from NATS_Python_Header import *

import copy
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import animation


RADIUS_EARTH_FT = 20925524.9;

#NATS_DIR = 'PLEASE_ENTER_NATS_LOCATION_HERE'
NATS_DIR = '.'

def compute_distance_gc(lat1,lon1,lat2,lon2,alt):
    lat1_rad = lat1*np.pi/180.;
    lon1_rad = lon1*np.pi/180.;
    lat2_rad = lat2*np.pi/180.;
    lon2_rad = lon2*np.pi/180.;

    sin_half_dlat = np.sin( .5*(lat1_rad - lat2_rad) );
    sin_half_dlon = np.sin( .5*(lon1_rad - lon2_rad) );
    cos_lat1 = np.cos(lat1_rad);
    cos_lat2 = np.cos(lat2_rad);
    x = sin_half_dlat*sin_half_dlat + cos_lat1 * cos_lat2 * sin_half_dlon*sin_half_dlon;
    return 2*(RADIUS_EARTH_FT + alt)*np.arcsin(np.sqrt(x));

def post_process_CDNR(dirPath):
    
    ac_list = ["SWA1897","SWA1192"];
    
    AllTrajs = {}
    for ac in ac_list:
        AllTrajs[ac] = [];
        
    for ac in ac_list:
        post_process = pp.PostProcessor(file_path = dirPath, \
                            ac_name = ac);
#     post_process.plotRoutine();
#         post_process.plotSingleAircraftTrajectory();
        AllTrajs[ac].extend(post_process.LatLonAltSamp)
    
    nfiles = len(AllTrajs[ac_list[0]])
    fig,axs = plt.subplots(nrows =2, ncols = 1)
    lv = []
    AllLon = []; AllLat = []; AllT = [];
    
    for file in range(nfiles):
        traj1 = copy.deepcopy(AllTrajs[ac_list[0]][file])
        traj2 = copy.deepcopy(AllTrajs[ac_list[1]][file])
        
        if len(traj1) > len(traj2):
            
            ntime = len(traj2)
            T = []
            RD = []
            Lat =[]
            Lon = []
            for k in range(ntime):
                val1 = [a for a in traj2[k]]
                idx = -1
                for j in range(len(traj1)):
                    if abs(traj1[j][0]-val1[0]) < 1e-3:
                        idx = j
                        break;
                
                if idx >=0:
                    val2 = [a for a in traj1[idx]]
                    T.append(val2[0]);
                    reldist = compute_distance_gc(val1[1], val1[2], val2[1], val2[2], (val1[3]+val2[3])/2.)
                    RD.append(reldist)
                    Lat.append([val1[1], val2[1]])
                    Lon.append([val1[2], val2[2]])
                
            line, = axs[0].plot(T,RD,'-x')
            lv.append(line)
            Lat = np.array(Lat)
            Lon = np.array(Lon)
            
            axs[1].plot(Lon[:,1],Lat[:,1],'--r')
            axs[1].plot(Lon[:,0],Lat[:,0],'--b')
            
            AllLat.append(Lat); AllLon.append(Lon); AllT.append(T)
            
        else:
            
            ntime = len(traj1)
            T = []
            RD = []
            Lat =[]
            Lon = []
                        
            for k in range(ntime):
                val1 = [a for a in traj1[k]]
                idx = -1
                for j in range(len(traj2)):
                    if abs(traj2[j][0]-val1[0]) <1e-3:
                        idx = j
                        break;
                
                if idx >=0:
                    val2 = [a for a in traj2[idx]]
                    T.append(val2[0]);
                    reldist = compute_distance_gc(val1[1], val1[2], val2[1], val2[2], (val1[3]+val2[3])/2.)
                    RD.append(reldist)
                    Lat.append([val1[1], val2[1]])
                    Lon.append([val1[2], val2[2]])
                
            line, = axs.plot(T,RD,'-x')
            lv.append(line)
            
            Lat = np.array(Lat)
            Lon = np.array(Lon)
            
            axs[1].plot(Lon[:,1],Lat[:,1],'--r')
            axs[1].plot(Lon[:,0],Lat[:,0],'--b')
            
            AllLat.append(Lat); AllLon.append(Lon); AllT.append(T)
    
    axs[0].set_xlabel('Time(s)');
    axs[0].set_ylabel('Relative distance between two aircraft (ft)')    
    axs[0].grid(True)
    
    axs[1].set_xlabel('Longitude (deg)')
    axs[1].set_ylabel('Latitude (deg)')
    axs[1].grid(True)
    
    
    lh = axs[0].axhline(5*6076,ls = '--')
#     fig.legend( (lv[0],lv[1],lh), ('w CDNR', 'w/o CDNR','resolution threshold'),
#                 'upper center', ncol = 3)
    
#     plt.show()    

    try:
        assert len(AllLat) == len(AllLon) == len(AllT) == 2
    except AssertionError:
        print('Please remove the *.csv files')
        raise
    
    frame_num = len(AllT[0])
    minlon = min( np.min(AllLon[0]),np.min(AllLon[1]))
    maxlon = max( np.max(AllLon[0]),np.max(AllLon[1]))
    
    minlat = min( np.min(AllLat[0]),np.min(AllLat[1]))
    maxlat = max( np.max(AllLat[0]),np.max(AllLat[1]))
    
    fig = plt.figure()
    ax = plt.axes(xlim=(minlon,maxlon), 
                  ylim=(minlat,maxlat)
                  )
    line11, = ax.plot([], [], linestyle = '--', color = 'r', marker = 'x', linewidth = 2)
    line12, = ax.plot([], [], linestyle = '--', color = 'g', marker = 'o', linewidth = 2)
    line21, = ax.plot([], [], linestyle = '--', color = 'k', marker = 'd', linewidth = 2)
    line22, = ax.plot([], [], linestyle = '--', color = 'b', marker = '+', linewidth = 2)
 
    lines = [line11,line12,line21,line22]
     
    def init():
        for line in lines:
            line.set_data([],[])
        return lines
     
    def animate(i):
         
        xlist = [AllLon[0][:i,0], AllLon[0][:i,1],AllLon[1][:i,0], AllLon[1][:i,1]]
        ylist = [AllLat[0][:i,0], AllLat[0][:i,1],AllLat[1][:i,0], AllLat[1][:i,1]]
         
        for lnum,line in enumerate(lines):
            line.set_data(xlist[lnum], ylist[lnum]) # set data for each line separately. 
 
        return lines

    # call the animator.  blit=True means only re-draw the parts that have changed.
    anim = animation.FuncAnimation(fig, animate, init_func=init,
                                   frames=frame_num, interval=10, blit=True)

    ax.set_xlabel('Longitude (deg)')
    ax.set_ylabel('Latitude (deg)')
    ax.grid(True)

    plt.show()
        
        
NauticalMilestoFeet = 6076.12

clsNATSStandalone = JClass('NATSStandalone')
# Start NATS Standalone environment
natsStandalone = clsNATSStandalone.start()

if (natsStandalone is None) :
    print "Can't start NATS Standalone"
    quit()
    
simulationInterface = natsStandalone.getSimulationInterface()

equipmentInterface = natsStandalone.getEquipmentInterface()
aircraftInterface = equipmentInterface.getAircraftInterface()

environmentInterface = natsStandalone.getEnvironmentInterface()
airportInterface = environmentInterface.getAirportInterface()
terminalAreaInterface = environmentInterface.getTerminalAreaInterface()

entityInterface = natsStandalone.getEntityInterface()
controllerInterface = entityInterface.getControllerInterface()

if not (os.path.isdir(NATS_DIR)) :
    print "Directory NATS_DIR does not exist"
    
elif simulationInterface is None :
    print "Can't get SimulationInterface"

else:
    output_dirname = "" # Reset
    orig_filename = "" # Reset
    
    CDNR_FLAG = [False,True]
     
    for flag in CDNR_FLAG:
        simulationInterface.clear_trajectory()
        environmentInterface.load_rap("share/tg/rap")
    
        aircraftInterface.load_aircraft("share/tg/trx/TRX_DEMO_CDNR_v1.5.trx", "share/tg/trx/TRX_DEMO_CDNR_mfl_v1.5.trx")

        simulationInterface.setupSimulation(36000, 30)

        # Set distance parameters of CDNR
        # These functions are optional.  The following values are default in NATS.
        # If users don't call these functions, NATS engine uses default values.
        #controllerInterface.setCDR_initiation_distance_ft_surface(600);
        #controllerInterface.setCDR_initiation_distance_ft_terminal(20 * NauticalMilestoFeet);
        #controllerInterface.setCDR_initiation_distance_ft_enroute(20 * NauticalMilestoFeet);
        #controllerInterface.setCDR_separation_distance_ft_surface(300);
        #controllerInterface.setCDR_separation_distance_ft_terminal(7 * NauticalMilestoFeet);
        #controllerInterface.setCDR_separation_distance_ft_enroute(10 * NauticalMilestoFeet);

        # Enable conflict detection and resolution
        controllerInterface.enableConflictDetectionAndResolution(flag);
    
        if (flag) :
            simulationInterface.start(3180)

            while True:
                runtime_sim_status = simulationInterface.get_runtime_sim_status()
                if (runtime_sim_status == NATS_SIMULATION_STATUS_PAUSE) :
                    break
                else:
                    time.sleep(1)
        
            # Result of CDR status is a 2-dimentional array
            # Array elements are: aircraft ID of the held aircraft
            #                     aircraft ID of the conflicting aircraft
            #                     seconds of holding of the held aircraft
            # Format type: [[String, String, float]]
            # Example: [["AC1", "AC_conflicting_with_AC1", heldSeconds_AC1], ["AC2", "AC_conflicting_with_AC2", heldSeconds_AC2]]
            array_cdrStatus = controllerInterface.getCDR_status()
            if not(array_cdrStatus is None) :
                print "Show CD&R Status:"
                for i in range(0, len(array_cdrStatus)) :
                    print "    AC1_held = ", array_cdrStatus[i][0]
                    print "    AC2_conflicting_with_AC1 = ", array_cdrStatus[i][1]
                    print "    heldSeconds_AC1 = ", array_cdrStatus[i][2]
        
            simulationInterface.resume()
        else :
            simulationInterface.start()
        
        # =====================================================================
        
        # Use a while loop to constantly check simulation status.  When the simulation finishes, continue to output the trajectory data
        while True:
            runtime_sim_status = simulationInterface.get_runtime_sim_status()
            if (runtime_sim_status == NATS_SIMULATION_STATUS_ENDED) :
                break
            else:
                time.sleep(1)
     
        millis = int(round(time.time() * 1000))
        
        if output_dirname == "":
            output_dirname = os.path.splitext(os.path.basename(__file__))[0] + "_" + str(millis)
            orig_filename = output_dirname
            output_dirname = "tmp_" + output_dirname
            os.makedirs(NATS_DIR + "/" + output_dirname)
        
        if flag:
            output_filename = orig_filename + "_CDNR.csv";
        else:
            output_filename = orig_filename + "_noCDNR.csv";
            
        print "Outputting trajectory data.  Please wait...."
        # Output the trajectory result file
        simulationInterface.write_trajectories(output_filename)

        aircraftInterface.release_aircraft()
        environmentInterface.release_rap()
        
        # Copy trajectory file to a temp directory
        copyfile(NATS_DIR + "/" + output_filename, NATS_DIR + "/" + output_dirname + "/" + output_filename)


# Stop NATS Standalone environment
natsStandalone.stop()

if not os.path.exists(NATS_DIR) :
    print "Directory NATS_DIR does not exist"
else :
    post_process_CDNR(NATS_DIR + "/" + output_dirname);

    # Delete temp directory
    print "Deleting directory:", output_dirname
    rmtree(NATS_DIR + "/" + output_dirname)

shutdownJVM()
