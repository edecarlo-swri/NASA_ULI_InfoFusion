"""Functions for reading Integrated Flight Format (IFF) files"""

import pandas as pd
import numpy as np
from pkg_resources import parse_version

def read_iff_file(filename, record_types=3, interp=False):
    """
    Read IFF file and return data frames for requested record types
    
    From IFF 2.15 specification, record types include:
    2: header
    3: track point
    4: flight plan
    5: data source program
    6: sectorization
    7: minimum safe altitude
    8: flight progress
    9: aircraft state

    Parameters
    ----------
    filename : str
    record_types : int, sequence of ints, or 'all'
        Record types to return.
    
    Returns
    -------
    DataFrame or dict of DataFrames
       If record_types is a scalar, return a DataFrame containing the
       data for that record type only.  Otherwise, return a dictionary
       mapping each requested record type to a corresponding DataFrame.
    """
    # Note default record_type of 3 (track point) is used for
    # consistency with the behavior of other functions that expect
    # flight tracking data

    # Determine file format version.  This is in record type 1, which
    # for now we assume to occur on the first line.
    with open(filename, 'r') as f:
        version = parse_version(f.readline().split(',')[2])

    # Columns for each record type, from version 2.6 specification.
    cols = {0:['recType','comment'],
            1:['recType','fileType','fileFormatVersion'],
            2:['recType','recTime','fltKey','bcnCode','cid','Source','msgType','AcId','recTypeCat','acType','Orig','Dest','opsType','estOrig','estDest'],
            3:['recType','recTime','fltKey','bcnCode','cid','Source','msgType','AcId','recTypeCat','coord1','coord2','alt','significance','coord1Accur','coord2Accur','altAccur','groundSpeed','course','rateOfClimb','altQualifier','altIndicator','trackPtStatus','leaderDir','scratchPad','msawInhibitInd','assignedAltString','controllingFac','controllingSeg','receivingFac','receivingSec','activeContr','primaryContr','kybrdSubset','kybrdSymbol','adsCode','opsType','airportCode'],
            4:['recType','recTime','fltKey','bcnCode','cid','Source','msgType','AcId','recTypeCat','acType','Orig','Dest','altcode','alt','maxAlt','assignedAltString','requestedAltString','route','estTime','fltCat','perfCat','opsType','equipList','coordinationTime','coordinationTimeType','leaderDir','scratchPad1','scratchPad2','fixPairScratchPad','prefDepArrRoute','prefDepRoute','prefArrRoute'],
            5:['recType','dataSource','programName','programVersion'],
            6:['recType','recTime','Source','msgType','rectypeCat','sectorizationString'],
            7:['recType','recTime','fltKey','bcnCode','cid','Source','msgType','AcId','recTypeCat','coord1','coord2','alt','significance','coord1Accur','coord2Accur','altAccur','msawtype','msawTimeCat','msawLocCat','msawMinSafeAlt','msawIndex1','msawIndex2','msawVolID'],
            8:['recType','recTime','fltKey','bcnCode','cid','Source','msgType','AcId','recTypeCat','acType','Orig','Dest','depTime','depTimeType','arrTime','arrTimeType'],
            9:['recType','recTime','fltKey','bcnCode','cid','Source','msgType','AcId','recTypeCat','coord1','coord2','alt','pitchAngle','trueHeading','rollAngle','trueAirSpeed','fltPhaseIndicator'],
            10:['recType','recTime','fltKey','bcnCode','cid','Source','msgType','AcId','recTypeCat','configType','configSpec']}

    # For newer versions, additional columns are supported.  However,
    # this code could be commented out, and it should still be
    # compatible with newer versions, but just ignoring the additional
    # columns.
    if version >= parse_version('2.13'):
        cols[2] += ['modeSCode']
        cols[3] += ['trackNumber','tptReturnType','modeSCode']
        cols[4] += ['coordinationPoint','coordinationPointType','trackNumber','modeSCode']
    elif version >= parse_version('2.15'):
        cols[3] += ['sensorTrackNumberList','spi','dvs','dupM3a','tid']

        
    # Read entire file and store as an array of lines:
    with open(filename, 'r') as f:
        data = f.readlines()

    # Create an array of the record types:
    line_record_types = [int(line.split(',')[0]) for line in data]
    del data

    #print('available record types:', np.unique(line_record_types))

    # Determine which record types to retrieve, and whether the result
    # should be a scalar or dict:
    if record_types == 'all':
        record_types = np.unique(line_record_types)
        scalar_result = False
    elif hasattr(record_types, '__getitem__'):
        scalar_result = False
    else:
        scalar_result = True
        record_types = [record_types]

    # For each record type, read the corresponding lines into a pandas
    # DataFrame:
    data_frames = dict()
    for record_type in record_types:
        # Get list of rows to skip
        skiprows = [i for i,lr in zip(range(len(line_record_types)), line_record_types) if lr != record_type]
        # Passing usecols is necessary because for some records, the
        # actual data has extraneous empty columns at the end, in
        # which case the data does not seem to get read correctly
        # without usecols
        df = pd.read_csv(filename, skiprows=skiprows, header=None, names=cols[record_type], low_memory=True, usecols=cols[record_type], na_values='?')

        # For consistency with other PARA-ATM data:
        df.rename(columns={'recTime':'time',
                           'AcId':'callsign',
                           'coord1':'latitude',
                           'coord2':'longitude',
                           'alt':'altitude',
                           'rateOfClimb':'rocd',
                           'groundSpeed':'tas',
                           'course':'heading'},
                  inplace=True)

        if 'time' in df:
            df['time'] = pd.to_datetime(df['time'], unit='s')
        if 'altitude' in df:
            df['altitude'] *= 100 # Convert 100s ft to ft

        # Store to dict of data frames
        data_frames[record_type] = df

    if scalar_result:
        result = data_frames[record_types[0]]
    else:
        result = data_frames

    return result

def get_departure_airport_from_iff(iff_data,callsign):
    origin_opts = []

    # Get all unique origin options from the iff_data set
    for key in iff_data.keys():
        df = iff_data[key][iff_data[key].callsign==callsign]    
        if 'Orig' in df.columns:
            df.dropna(axis=0,subset=['Orig'],inplace=True)
            origin_opts.extend([orig for orig in list(df.Orig.unique()) if not orig=='nan'])
        if 'estOrig' in df.columns:
            df.dropna(axis=0,subset=['estOrig'],inplace=True)
            origin_opts.extend([orig for orig in list(df.estOrig.unique()) if not orig=='nan'])

    # In the case of multiple origin options names, take the first one
    if len(origin_opts)>0:
        origin = list(set((origin_opts)))[0]
    else:
        origin = []

    # Add K to the front of an airport code to make it compatible with NATS
    if len(origin)==3:
        origin = 'K'+origin
        
    if len(origin) == 4:
        # Check that airport code begins with 'K'
        check = origin[0]=='K'
        if check:
            return origin
    else:
        #TODO: Decide what to do if no airport is found
        print("No viable departure airport found for {}. Returning 'None'.".format(callsign))
        return None
        

def get_arrival_airport_from_iff(iff_data,callsign):
    dest_opts = []

    # Get all unique origin options from the iff_data set
    for key in iff_data.keys():
        df = iff_data[key][iff_data[key].callsign==callsign]    
        if 'Dest' in df.columns:
            df.dropna(axis=0,subset=['Dest'],inplace=True)
            dest_opts.extend([orig for orig in list(df.Dest.unique()) if not orig=='nan'])
        if 'estDest' in df.columns:
            df.dropna(axis=0,subset=['estDest'],inplace=True)
            dest_opts.extend([orig for orig in list(df.estDest.unique()) if not orig=='nan'])
    # In the case of multiple origin options names, take the first one

    if len(dest_opts)>0:
        dest = list(set(dest_opts))[0]
    else:
        dest = []
        
    # Add K to the front of an airport code to make it compatible with NATS
    if len(dest)==3:
        dest = 'K'+dest
        
    if len(dest) == 4:
        # Check that airport code begins with 'K'
        check = dest[0]=='K'
        if check:
            return dest
    else:
        #TODO: Decide what to do if no airport is found
        print("No viable destination airport found for {}. Returning 'None'.".format(callsign))
        return None
    
def check_if_flight_has_departed(iff_data,callsign):
    return False
     
