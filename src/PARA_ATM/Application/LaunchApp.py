'''

NASA NextGen NAS ULI Information Fusion
        
@organization: PARA Lab, Arizona State University (PI Dr. Yongming Liu)
@author: Hari Iyer
@date: 01/19/2018

Run this module to invoke the application. It contains the main features and functions to execute the system.

'''

import sys

sys.path.insert(0, '/home/dyn.datasys.swri.edu/mhartnett/NASA_ULI/NASA_ULI_InfoFusion/src/')

from PARA_ATM import *
from PARA_ATM.Commands import readNATS,readIFF,readTDDS
import time

class GitHub(QWidget):
    '''
        When instantiated, this class provides a view of the GitHub Code repository
        and documentation for reference.
    '''
    def __init__(self):
        
        #Initialize the popup window
        QWidget.__init__(self)
        self.githubPopup = QWidget() 
        self.githubView = QWebView()
        
        #Set URL to the project GitHub resource
        self.githubView.setUrl(QUrl("https://github.com/ymlasu/NASA_ULI_InfoFusion"))
        self.githubLayout = QVBoxLayout(self)
        
        #Add the view to main application
        self.githubLayout.addWidget(self.githubView)



class ParaATM(QWidget):
    '''
        Class ParaATM wraps the entire application together with all the layout and features tied 
        together with the functionality.
    '''
    def __init__(self):
        
        self.NATS_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)),'../../NATS/Server/')
        self.SHERLOCK_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)),'../../../data/Sherlock/')
        #Initialize application window
        self.application = QApplication(sys.argv)
        self.window = QWidget()
        self.mapView = QWebView()
        super(ParaATM, self).__init__()
        
        #Set connection to postgres database based on the credentials mentioned
        self.connection = psycopg2.connect(database="paraatm", user="paraatm_user", password="paraatm_user", host="localhost", port="5432")
        self.cursor = self.connection.cursor()
        
        #Application-level data definition
        self.flightSelected = ""
        self.tableList = sorted(self.getTableList())
        self.dateRangeSelected = []
        self.commandParameters = []
        self.filterToggles = list(range(1, 5))
        
        #Build and launch application UI
        self.buildUI()
        
    def menu_trajectory(self):
        action = self.sender()
        acid = action.text()
        table = action.parent().title()
        if os.path.exists(self.NATS_DIR+table):
            cmd = readNATS.Command(self.cursor,[table,'callsign='+acid])
        elif os.path.exists(self.SHERLOCK_DIR+table):
            cmd = readIFF.Command(self.cursor,[table,'callsign='+acid])
        self.commandParameters = cmd.executeCommand()
        self.initMap()

    '''
        buildUI() adds the UI elements and includes definitions for functional execution
    '''
    def buildUI(self):
        
        #Setting UI layouts
        self.layoutMain = QVBoxLayout()
        self.menuLayout = QHBoxLayout()
        self.mapLayout = QHBoxLayout()
        self.flightSelectionLayout = QVBoxLayout()
        self.actionsLayout = QVBoxLayout()
        self.liveFlightsLayout = QVBoxLayout()
        
        #Make menu
        bar = QMenuBar()
        display = bar.addMenu("View")
        for table in self.tableList:
            dataset = display.addMenu(table)
            query = "SELECT DISTINCT callsign FROM \"%s\""%table
            self.cursor.execute(query)
            flightList = [i[0] for i in self.cursor.fetchall()]
            for acid in flightList:
                action = dataset.addAction(acid)
                action.triggered.connect(self.menu_trajectory)

        self.menuLayout.addWidget(bar)

        #Populate table list for trajectory selection
        self.tablePickerLayout = QHBoxLayout()    
        self.tableSelection = QComboBox()
        self.tableSelection.addItems(self.tableList)
        self.tablePickerLayout.addWidget(QLabel("Available Tables: "))
        self.tablePickerLayout.addWidget(self.tableSelection)
        
        def show_trajectory():
            table = self.tableSelection.currentText()
            acid = self.flightSelection.currentText()
            if os.path.exists(self.NATS_DIR+table):
                cmd = readNATS.Command(self.cursor,[table,'callsign='+acid])
            elif os.path.exists(self.SHERLOCK_DIR+table):
                cmd = readIFF.Command(self.cursor,[table,'callsign='+acid])
            self.commandParameters = cmd.executeCommand()
            self.initMap()

        def populate_flights():
            query = "SELECT DISTINCT callsign FROM \"%s\""%self.tableSelection.currentText()
            self.cursor.execute(query)
            flightList = sorted([i[0] for i in self.cursor.fetchall()])
            if self.flightPickerLayout:
                self.flightSelectionLayout.removeItem(self.flightPickerLayout)
            self.flightPickerLayout = QHBoxLayout()
            self.flightSelection = QComboBox()
            self.flightSelection.addItems(flightList)
            self.flightPickerLayout.addWidget(QLabel("Flights: "))
            self.flightPickerLayout.addWidget(self.flightSelection)
            self.flightSelection.activated.connect(show_trajectory)
            self.flightSelectionLayout.addLayout(self.flightPickerLayout)

        self.flightPickerLayout=None
        self.tableSelection.activated.connect(populate_flights)
        '''
        #Data range start for trajectory plotting
        self.fromDatePicker = QHBoxLayout()
        self.simulationStartMonth = QComboBox(self)
        self.simulationStartDate = QComboBox(self)
        self.simulationStartYear = QComboBox(self)
        self.fromDatePicker.addWidget(QLabel("From: "))
        self.fromDatePicker.addWidget(self.simulationStartMonth)
        self.fromDatePicker.addWidget(self.simulationStartDate)
        self.fromDatePicker.addWidget(self.simulationStartYear)
        
        #Data range end for trajectory plotting
        self.toDatePicker = QHBoxLayout()
        self.simulationEndMonth = QComboBox(self)
        self.simulationEndDate = QComboBox(self)
        self.simulationEndYear = QComboBox(self)
        self.toDatePicker.addWidget(QLabel("To:     "))
        self.toDatePicker.addWidget(self.simulationEndMonth)
        self.toDatePicker.addWidget(self.simulationEndDate)
        self.toDatePicker.addWidget(self.simulationEndYear)
        
        #Widget size scaling for better UI
        #self.flightSelection.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.simulationStartMonth.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.simulationStartDate.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.simulationStartYear.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.simulationEndMonth.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.simulationEndDate.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.simulationEndYear.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        #Adding date picker UI elements and populate them
        for month in months:
            self.simulationStartMonth.addItem(month)
            self.simulationEndMonth.addItem(month)
        for date in dates:
            self.simulationStartDate.addItem(date)
            self.simulationEndDate.addItem(date)
        for year in years:
            self.simulationStartYear.addItem(year)
            self.simulationEndYear.addItem(year)
        
        #Button to trigger and plot trajectories
        self.plotButton = QPushButton("Plot Trajectory")
        self.plotButton.clicked.connect(self.plotTrajectory)
        '''
        #Add flight selection widgets to UI
        self.flightSelectionLayout.addLayout(self.tablePickerLayout)
        
        '''
        self.flightSelectionLayout.addLayout(self.fromDatePicker)
        self.flightSelectionLayout.addLayout(self.toDatePicker)
        self.flightSelectionLayout.addWidget(self.plotButton)
        '''

        #Command line UI elements with action upon execution request
        self.commandInput = QLineEdit()
        self.commandInput.returnPressed.connect(self.executeCommand)
        #self.commandExecute = QPushButton("Execute Command")
        #self.commandExecute.clicked.connect(self.executeCommand)
        self.actionsLayout.addWidget(QLabel("Command Line: "))
        self.actionsLayout.addWidget(self.commandInput)
        #self.actionsLayout.addWidget(self.commandExecute)
        
        #Adding toggles for map filters and overlays with action upon execution request
        self.filterLayoutOptions = QHBoxLayout()
        self.filterLayoutControls = QVBoxLayout()
        self.weatherToggle = QCheckBox("Weather")
        self.airportToggle = QCheckBox("Airports")
        self.waypointToggle = QCheckBox("Waypoints")
        self.sectorToggle = QCheckBox("Sectors")
        self.filterLayoutOptions.addWidget(self.weatherToggle)
        self.filterLayoutOptions.addWidget(self.airportToggle)
        self.filterLayoutOptions.addWidget(self.waypointToggle)
        self.filterLayoutOptions.addWidget(self.sectorToggle)
        self.applyFilters = QPushButton("Apply Filters")
        self.applyFilters.clicked.connect(self.plotTrajectory)
        self.filterLayoutControls.addLayout(self.filterLayoutOptions)
        self.filterLayoutControls.addWidget(self.applyFilters)
        self.actionsLayout.addLayout(self.filterLayoutControls)
        
        #Query air crash ontology from the application UI
        self.ontologyQuery = QLineEdit()
        self.runQuery= QPushButton("Run Query")
        self.liveFlightsLayout.addWidget(self.ontologyQuery)
        self.liveFlightsLayout.addWidget(self.runQuery)
        
        #Live flights view
        self.liveFlights = QPushButton("Live Flights")
        self.liveFlights.clicked.connect(self.liveFlightsLayer)
        self.liveFlights.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        #Help and documentation access from the application
        self.helpButton = QPushButton("Documentation and Help")
        self.helpButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        #Button click action definitions
        self.runQuery.clicked.connect(self.queryOntology)
        self.helpButton.clicked.connect(self.openGitHub)
        
        self.liveFlightsLayout.addWidget(self.liveFlights)
        self.liveFlightsLayout.addWidget(self.helpButton)
        
        #Initialize map based on the constraints and parameters provided above
        self.initMap()
        
        #Add parent elements to the base UI
        self.menuLayout.addLayout(self.flightSelectionLayout)
        self.menuLayout.addLayout(self.actionsLayout)
        self.menuLayout.addLayout(self.liveFlightsLayout)
        self.layoutMain.addLayout(self.menuLayout)
        self.layoutMain.addLayout(self.mapLayout)
        
        #Show application window
        self.window.setLayout(self.layoutMain)
        self.window.setWindowTitle("PARA-ATM")
        self.window.showMaximized()
        self.window.show()
        sys.exit(self.application.exec_())
        
    '''
        initmap() pulls in the leaflet map to the application from MapView module.
    '''
    def initMap(self):
        
        #Set the toggle values based on user selection
        self.filterToggles[0] = 1 if self.airportToggle.isChecked() else 0
        self.filterToggles[1] = 1 if self.waypointToggle.isChecked() else 0
        self.filterToggles[2] = 1 if self.weatherToggle.isChecked() else 0
        self.filterToggles[3] = 1 if self.sectorToggle.isChecked() else 0
        
        #Invoke MapView to plot the map onto the application layout based on the user's preferences as parameters
        self.mapHTML = MapView.buildMap(self.flightSelected, self.dateRangeSelected, self.filterToggles, self.cursor, self.commandParameters)
        self.mapView.setHtml(self.mapHTML)
        self.mapLayout.addWidget(self.mapView)

    '''
        getTableList() fetches the callsign list of flights to be displayed for selection
    '''
    def getTableList(self):
        
        #Execute query to fetch flight data
        query = "SELECT t.table_name \
                 FROM information_schema.tables t \
                 JOIN information_schema.columns c ON c.table_name = t.table_name \
                 WHERE c.column_name LIKE 'callsign'"
        self.cursor.execute(query)
        results = self.cursor.fetchall()
        return [result[0] for result in results]
        
    '''
        plotTrajectory() is used to either initialize, or update the trajectory plot upon a new  
        every request 
    '''
    def plotTrajectory(self):
        
        #Formulate date range and flight from selection
        self.dateRangeSelected = []
        self.flightSelected = self.flightSelection.currentText()
        self.startDateSelected = self.simulationStartYear.currentText() + "-" + self.simulationStartMonth.currentText() + "-" + self.simulationStartDate.currentText()
        self.endDateSelected = self.simulationEndYear.currentText() + "-" + self.simulationEndMonth.currentText() + "-" + self.simulationEndDate.currentText()
        fromDate = datetime.date(int(self.simulationStartYear.currentText()), int(self.simulationStartMonth.currentText()), int(self.simulationStartDate.currentText()))
        toDate = datetime.date(int(self.simulationEndYear.currentText()), int(self.simulationEndMonth.currentText()), int(self.simulationEndDate.currentText()))
        
        #Update to new trajectory parameters
        for dateInstance in self.flightDateRange(fromDate, toDate):
            self.dateRangeSelected.append(dateInstance.strftime("%Y-%m-%d"))
        
        #Plot or re-plot trajectory data
        self.initMap()
        
    '''
        flightDateRange() returns a list of dates between two selected dates
    '''
    def flightDateRange(self, fromDate, toDate):
        for n in range(int ((toDate - fromDate).days) + 1):
            yield fromDate + datetime.timedelta(n)
            
    '''
        liveFlightsLayer() overlays the live flight map onto the application layout
    '''
    def liveFlightsLayer(self):
        self.mapView.setUrl(QUrl(str(Path(__file__).parent.parent) + "/Map/web/LiveFlights.html"))

    '''
        openGitHub() pops up the help window with the code documentation and repository
    '''
    def openGitHub(self):
        self.githubPopup = GitHub()
        self.githubPopup.setWindowTitle("PARA-ATM Help")
        self.githubPopup.show()
        
    '''
        queryOntology() shows up the results from the ontology search in a popup window. This function 
        is under development for completeness.
    '''
    def queryOntology(self):
        
        #Invoke the QueryOntology class method to run the query
        queryOutput = QueryOntology.query()
        
        #Display output in popup window
        outputDisplay = QLabel(queryOutput)
        outputDisplay.show()
        
    '''
        executeCommand() calls the relevant command code under the Commands package.
    '''
    def executeCommand(self):
        
        #Get the command name and argument inputs
        commandInput = self.commandInput.text() 
        commandName = str(commandInput.split('(')[0])
        cmd = getattr(__import__('PARA_ATM.Commands',fromlist=[commandName]), commandName)
        commandArguments = str(commandInput.split('(')[1])[:-1]
        if ',' in commandArguments:
            commandArguments = commandArguments.split(',')
        if commandName == 'groundSSD':
            commandClass = cmd.Command(self.cursor,self,commandArguments)
        else:
            commandClass = cmd.Command(self.cursor, commandArguments)
        self.commandParameters = commandClass.executeCommand()
        print('command %s executed'%commandName)
        
        #Command specific conditions
        if (commandName == "Airport"):
            self.mapView.setUrl(QUrl(str(Path(__file__).parent.parent) +  "/Map/web/LiveFlights.html?latitude=" + self.commandParameters[1] + "&longitude=" + self.commandParameters[2]))
        elif (commandName == "NATS_GateToGateSim"):
            parentPath = str(Path(__file__).parent.parent.parent)
            with open(str(parentPath) + "/NATS/Server/DEMO_Gate_To_Gate_SFO_PHX_trajectory_beta_1.0.csv", 'r') as content_file:
                CSVData = content_file.read()
            w = QWidget()
            try:
                result = QMessageBox.question(w, 'NATS Output', "" + str(CSVData)[0:5000])
            except:
                print('NATS output error')
                raise Exception
            w.showFullScreen()
        elif commandName=='groundSSD':
            print(self.commandParameters[1])
        else:
            self.initMap()
            print(self.commandParameters[1])

'''
    main() instantiates the ParaATM Class to run the application
'''
def main():
    paraAtm = ParaATM()

if __name__ == '__main__':
    main()
