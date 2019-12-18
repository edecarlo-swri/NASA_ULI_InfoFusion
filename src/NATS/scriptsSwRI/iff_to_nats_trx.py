from NATS import NATS_Config

import PARA_ATM
from sys import argv
from trx_tools import write_base_trx
import numpy as np

track_file = "../../../../Documents/nats_analyses/trx/cs_aal343.trx"
mfl_file = "../../../../Documents/nats_analyses/trx/cs_aal343_mfl.trx"
nats = NATS_Config(track_file=track_file,max_flt_lev_file = mfl_file)

iff_data = PARA_ATM.utils.read_data_file("../PARA_ATM/sample_data/IFF_SFO_ASDEX_ABC123.csv",record_types=[2,3,4])

for callsign in iff_data[3].callsign.unique():

    departureAirport = PARA_ATM.iff.get_departure_airport_from_iff(iff_data,callsign)
    arrivalAirport = PARA_ATM.iff.get_arrival_airport_from_iff(iff_data,callsign)

    flightTakenOff = PARA_ATM.iff.check_if_flight_has_departed(iff_data,callsign)
    departureAirportElevation = nats.airportInterface.select_airport(departureAirport).getElevation()/100.
    
    trackData = iff_data[3].loc[((iff_data[3].callsign==callsign) & (iff_data[3].altitude < departureAirportElevation + 50./100.)),:].copy()

    trackData.loc[:,'airportNodes']= [PARA_ATM.nats.get_closest_node_at_airport(lat,lon,departureAirport) for lat,lon in zip(trackData.latitude,trackData.longitude)]
    # unique_nodes = trackData.airportNodes.unique()
    # adjacent_nodes = {}
    # for i,node in enumerate(unique_nodes):
    #     adjacent_nodes[node] = PARA_ATM.nats.get_list_of_adjacent_nodes(node,departureAirport)

    
# fname = 'trxSwRI/cs_aal343'
# write_base_trx(iff_data,fname)

#To do: get cs_aal343 and write initial .trx and .mfl files in share/tg/trx, then load them into the aircraftInterface. We only care about the departure airport, the arrival airport can be PHX.

# #fname = 'trxSwRI/TRX_DEMO_Combined_GateToGate'
# # #Custom TRX can be set here
# aircraftInterface.load_aircraft("{}.trx".format(fname), "{}_mfl.trx".format(fname))

# # # Get callsigns of all flights in the TRX
# callsignList = aircraftInterface.getAllAircraftId()
# print('CALLSIGN LIST: ', callsignList)

# for callsign in callsignList:
#     departureAirport = airportInterface.getDepartureAirport(callsign)
#     arrivalAirport = airportInterface.getArrivalAirport(callsign)
#     flight = aircraftInterface.select_aircraft(callsign)

#     print('departureAirport: ', departureAirport)
#     print('arrivalAirport: ', arrivalAirport)

# # Iterate through flights to generate Gate to Gate flight plans and store them in the TRX file.
# for callsign in callsignList:
    
#     print("Augmented flight plan generation for aircraft: " + callsign)
#     print("-----------------------------------------------------------")
    
#     ### To do: Decide what happens for flights that have already departed.
#     flightTakenOff = 'no';
        
#     # Get flight instance for the callsign name
#     flight = aircraftInterface.select_aircraft(callsign)
    
#     # Get arrival and destination airports
#     departureAirport = airportInterface.getDepartureAirport(callsign)
#     arrivalAirport = airportInterface.getArrivalAirport(callsign)

#     # Get arrival and departure airport gates
#     departureGates = []
#     if (flightTakenOff == "no"):
#         departureGates = list(airportInterface.getAllGates(departureAirport))

#     arrivalGates = list(airportInterface.getAllGates(arrivalAirport))
    
#     # Get arrival and departure airport runways
#     departureRunways = {}
#     if (flightTakenOff == "no"):
#         departureRunways = {key.replace(" ", ""): value.replace(" ", "") for (key, value) in  airportInterface.getAllRunways(departureAirport)}
#     arrivalRunways =  {key.replace(" ", ""): value.replace(" ", "") for (key, value) in airportInterface.getAllRunways(arrivalAirport)}
    
#     selectedDepartureGate = ""
#     selectedDepartureRunway = ""

#     departureRunwayID = selectedDepartureRunway
#     arrivalRunwayID = selectedArrivalRunway
    
#     if selectedDepartureRunway:
#         selectedDepartureRunway = departureRunways[selectedDepartureRunway]
        
#     runwayEnds = airportInterface.getRunwayEnds(arrivalAirport, selectedArrivalRunway)
#     if not runwayEnds:
#         runwayEnds = airportInterface.getRunwayEnds(arrivalAirport, selectedArrivalRunway + " ")
#     selectedArrivalRunway = list(runwayEnds)[1]
    
    
#     departureTaxi = []
#     if (flightTakenOff == "no"):
#         departureTaxi = airportInterface.get_taxi_route_from_A_To_B(callsign, departureAirport, selectedDepartureGate, selectedDepartureRunway)

#     arrivalTaxi = airportInterface.get_taxi_route_from_A_To_B(callsign, arrivalAirport, selectedArrivalRunway, selectedArrivalGate)
    
#     sidProcedures = []
#     selectedSidProcedure = []
#     if (flightTakenOff == "no"):
        
#         # Get all SID procedures for departure airport
#         sidProcedures = terminalAreaInterface.getAllSids(departureAirport)
#         if not sidProcedures:
#             print(departureAirport + " has no SID procedures.\n")
#             selectedSidProcedure = ""
            
#         else:
#             while 1:
#                 selectedSidProcedure = raw_input("Please choose a SID procedure for departure from " + departureAirport + " among [" + ",".join(sidProcedures) + "]: ")
#                 if selectedSidProcedure not in sidProcedures:
#                     print("\nInvalid SID procedure selected, please try again.\n")
#                 else: 
#                     print("\n")
#                     break


#     # Get Enroute waypoints in flight plan
#     enrouteWaypoints = raw_input("Please enter enroute waypoints in flight plan separated by ',' (Eg. BOILE,LOSHN,BLH): ")
    
#     # Get all STAR procedures for arrival airport
#     starProcedures = terminalAreaInterface.getAllStars(arrivalAirport)
#     while 1:
#         selectedStarProcedure = raw_input("\nPlease choose a STAR procedure for arrival into " + arrivalAirport + " among [" + ",".join(starProcedures) + "]: ")
#         if selectedStarProcedure not in starProcedures:
#             print("\nInvalid STAR procedure selected, please try again.\n")
#         else: 
#             print("\n")
#             break

#     # Get all APPROACH procedures for arrival airport
#     approachProcedures = terminalAreaInterface.getAllApproaches(arrivalAirport)
#     while 1:
#         selectedApproachProcedure = raw_input("Please choose an Approach procedure for arrival into " + arrivalAirport + " among [" + ",".join(approachProcedures) + "]: ")
#         if selectedApproachProcedure not in approachProcedures:
#             print("\nInvalid Approach procedure selected, please try again.\n")
#         else: 
#             print("\n")
#             break

    
#     # Flight plan string generation
#     if (not departureTaxi and flightTakenOff == "no"):
#         print("No default departure taxi route available, please refer to functions getLayout_node_map(String airport_code) and getLayout_node_data(String airport_code) in API Documentation for airport ground nodes to build a taxi plan.\n")
#         departureTaxi = []
#     if (not arrivalTaxi):
#         print("No default arrival taxi route available, please refer to functions getLayout_node_map(String airport_code) and getLayout_node_data(String airport_code) in API Documentation for airport ground nodes to build a taxi plan.\n")
#         arrivalTaxi = []
    
#     if (flightTakenOff == "no") :
#         augmentedFlightPlan = departureAirport + ".<"
#     else :
#         augmentedFlightPlan = departureAirport + "./"
    
#     for airportGroundNode in departureTaxi:
#         augmentedFlightPlan = augmentedFlightPlan + "{\"id\": \"" + airportGroundNode + "\"}, "
        
#     if (len(departureTaxi) > 0 and selectedSidProcedure is not ""):
#         augmentedFlightPlan = augmentedFlightPlan[:-2]
#         augmentedFlightPlan += ">." + departureRunwayID + "." + selectedSidProcedure + "." + enrouteWaypoints.replace(",", "..") + "." + selectedStarProcedure + "." + selectedApproachProcedure + "." + arrivalRunwayID + ".<"
    
#     elif (len(departureTaxi) > 0 and selectedSidProcedure is ""):
#         augmentedFlightPlan = augmentedFlightPlan[:-2]
#         augmentedFlightPlan += ">." + departureRunwayID + "." + enrouteWaypoints.replace(",", "..") + "." + selectedStarProcedure + "." + selectedApproachProcedure + "." + arrivalRunwayID + ".<"
#     else:
#         augmentedFlightPlan += "." + enrouteWaypoints.replace(",", "..") + "." + selectedStarProcedure + "." + selectedApproachProcedure + "." + arrivalRunwayID + ".<"

#     for airportGroundNode in arrivalTaxi:
#         augmentedFlightPlan = augmentedFlightPlan + "{\"id\": \"" + airportGroundNode + "\"}, "
    
#     if(len(arrivalTaxi) > 0):
#         augmentedFlightPlan = augmentedFlightPlan[:-2]
#     augmentedFlightPlan += ">." + arrivalAirport
    
#     print("The augmented flight plan for flight " + callsign + " is as follows. FP_ROUTE value in the original TRX can be replaced by this flight plan.")
#     print(augmentedFlightPlan)
#     print("\n\n")
        
# # aircraftInterface.release_aircraft()
# environmentInterface.release_rap()

# # Stop NATS Standalone environment
# natsStandalone.stop()

# shutdownJVM()
