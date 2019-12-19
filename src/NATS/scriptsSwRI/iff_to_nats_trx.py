from NATS import NATS_Config

from PARA_ATM.io import iff, nats, utils
from sys import argv
from trx_tools import write_base_trx
import numpy as np

track_file = "../../../../Documents/nats_analyses/trx/cs_aal343.trx"
mfl_file = "../../../../Documents/nats_analyses/trx/cs_aal343_mfl.trx"
natsSim = NATS_Config(track_file=track_file,max_flt_lev_file = mfl_file)

iff_data = utils.read_data_file("../PARA_ATM/sample_data/IFF_SFO_ASDEX_ABC123.csv",record_types=[2,3,4])

for callsign in iff_data[3].callsign.unique():

    departureAirport = iff.get_departure_airport_from_iff(iff_data,callsign)
    arrivalAirport = iff.get_arrival_airport_from_iff(iff_data,callsign)

    flightTakenOff = iff.check_if_flight_has_departed(iff_data,callsign,natsSim,departureAirport)

    if not flightTakenOff:
        departureAirportElevation=natsSim.airportInterface.select_airport(departureAirport).getElevation()
        trackData = iff_data[3].loc[((iff_data[3].callsign==callsign) & (iff_data[3].altitude < departureAirportElevation + 50.)),:].copy()
        txt = iff.create_gate_to_runway_from_iff(trackData,natsSim,departureAirport)
    else:
        print('Still need to do gate to gate flight plans for landing aircraft.')
    
