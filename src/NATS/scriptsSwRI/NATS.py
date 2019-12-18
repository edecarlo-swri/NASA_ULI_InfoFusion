import os
import jpype as jp

env_NATS_HOME = os.environ.get('NATS_HOME')

str_NATS_HOME = ""

if not(env_NATS_HOME is None) :
    str_NATS_HOME = env_NATS_HOME + "/"

classpath = str_NATS_HOME + "dist/nats-standalone.jar"
classpath = classpath + ":" + str_NATS_HOME + "dist/nats-client.jar"
classpath = classpath + ":" + str_NATS_HOME + "dist/nats-shared.jar"
classpath = classpath + ":" + str_NATS_HOME + "dist/json.jar"
classpath = classpath + ":" + str_NATS_HOME + "dist/commons-logging-1.2.jar"

jp.startJVM(jp.getDefaultJVMPath(), "-ea", "-Djava.class.path=%s" % classpath)

class NATS_Config:
    def __init__(self, duration = 86400,
                 interval = 1,
                 client_dir = env_NATS_HOME,
                 wind_dir = 'share/tg/rap',
                 track_file = "share/tg/trx/swim_example_aug.trx",
                 max_flt_lev_file = "share/tg/trx/swim_example_mfl.trx"):
        self.endTime = duration
        self.interval = interval
        self.initializeJVM()
        self.wind_dir = wind_dir
        self.trx_file = track_file
        self.mfl_file = max_flt_lev_file

    '''Initialize the NATS client'''
    def initializeJVM(self):

        self.NATS_SIMULATION_STATUS_ENDED = jp.JPackage('com').osi.util.Constants.NATS_SIMULATION_STATUS_ENDED;
        clsNATSStandalone = jp.JClass('NATSStandalone')

        # Start NATS Standalone environment
        self.natsClient = clsNATSStandalone.start()

        if (self.natsClient is None) :
            print("Can't start NATS Standalone")
            quit()

        self.equipmentInterface = self.natsClient.getEquipmentInterface()

        # Get EnvironmentInterface
        self.environmentInterface = self.natsClient.getEnvironmentInterface()
        # Get AirportInterface
        self.airportInterface = self.environmentInterface.getAirportInterface()
        # Get TerminalAreaInterface
        self.terminalAreaInterface = self.environmentInterface.getTerminalAreaInterface()
        self.sim = self.natsClient.getSimulationInterface()
        
        self.aircraftInterface = self.equipmentInterface.getAircraftInterface()
        self.entityInterface = self.natsClient.getEntityInterface()
        self.controllerInterface = self.entityInterface.getControllerInterface()
        self.pilotInterface = self.entityInterface.getPilotInterface()

