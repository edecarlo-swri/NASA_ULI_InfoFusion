"""Functions for interfacing to NATS simulation"""

import os
import pandas as pd
import numpy as np
from io import StringIO
import os
import jpype
import tempfile


def get_nats_constant(name):
    """Return the variable that stores the named NATS constant
    
    This must be called while the JVM is running, e.g., within a
    NatsSimulationWrapper instance
    """
    return getattr(jpype.JPackage('com').osi.util.Constants, name)

class NatsSimulationWrapper:
    """Parent class for creating a NATS simulation instance

    This class handles path issues behind the scenes, making it
    possible to run NATS from any directory, with output files being
    written back to the current working directory.

    Users should implement the following methods in the derived class:
    
    simulation: This method runs the actual NATS simulation.  The user
        can assume that the jvm is already started and that it will be
        shutdown by the parent class.  If the simulation code needs to
        access data files relative to the original working directory,
        use the get_path method, which will produce an appropriate
        path to work around the fact that NATS simulation occurs in
        the NATS_HOME directory.

    write_output: This method writes output to the specified filename.

    cleanup: Cleanup code that will be called after simulation and
        write_output.  Having cleanup code in a separate method makes
        it possible for cleanup to occur after write_output.

    """
    def __init__(self, nats_home=None):
        """
        Parameters
        ----------
        nats_home : str
            Full path to NATS home directory.  This will override the
            NATS_HOME environment variable, if it exists.
        """
        if nats_home is None:
            self.NATS_HOME = os.environ.get('NATS_HOME')
            if self.NATS_HOME is None:
                raise RuntimeError('either NATS_HOME environment variable must be set, or nats_home argument must be provided')
        else:
            self.NATS_HOME = nats_home

    def simulation(self, *args, **kwargs):
        """Users must implement this method in the derived class

        Assume that the jvm is already started and that it will be
        shutdown by the parent class.
        """
        raise NotImplementedError("derived class must implement 'simulation' method")

    def write_output(self, filename):
        """Users must implement this method in the derived class

        It will be called after the simulation method and should issue
        the commands necessary to write the output to the specified
        file.
        """
        raise NotImplementedError("derived class must implement 'write_output' method")

    def __call__(self, output_file=None, return_df=True, *args, **kwargs):

        """Execute NATS simulation and write output to specified file

        Parameters
        ----------
        output_file : str
            Output file to write to.  If not provided, a temporary file is used
        return_df : bool
            Whether to read the output into a DataFrame and return it

        Returns
        -------
        DataFrame
            If return_df is True, read the output into a DataFrame and
            return that
        """
        self.cwd = os.getcwd() # Save current working directory

        # It is necssary to change directories because the NATS
        # simulation issues a system call to "./run"
        os.chdir(os.path.abspath(self.NATS_HOME))
        
        self._start_jvm()

        try:
            self.simulation(*args, **kwargs)

            # Go back to where we where.  Even though this is issued prior
            # to writing output, the NATS commands that write output still
            # seem to treat NATS_HOME as the working directory.  The
            # workaround is that the user code can form an absolute path
            # using the cwd attribute.
            os.chdir(self.cwd)

            if output_file is None:
                # Create a temporary directory to store the output, so it
                # can be read back
                tempdir = tempfile.mkdtemp()
                output_file = os.path.join(tempdir, 'nats.csv')
            else:
                tempdir = None

            try:
                self.write_output(self.get_path(output_file))
                if return_df:
                    df = read_nats_output_file(output_file)
            finally:
                # This ensures we clean up the temporary directory and
                # file even if an exception occurs above.  If there is an
                # exception, it is automatically re-raised after finally.
                if tempdir:
                    if os.path.isfile(output_file):
                        os.remove(output_file)
                    os.rmdir(tempdir)

            if hasattr(self, 'cleanup'):
                self.cleanup()

        finally:
            # Make sure that jvm gets stopped even if an exception occurs
            self._stop_jvm()

        if return_df:
            return df

    def _start_jvm(self):
        classpath = self.NATS_HOME + "dist/nats-standalone.jar"
        classpath = classpath + ":" + self.NATS_HOME + "dist/nats-client.jar"
        classpath = classpath + ":" + self.NATS_HOME + "dist/nats-shared.jar"
        classpath = classpath + ":" + self.NATS_HOME + "dist/json.jar"
        classpath = classpath + ":" + self.NATS_HOME + "dist/commons-logging-1.2.jar"

        jpype.startJVM(jpype.getDefaultJVMPath(), "-ea", "-Djava.class.path=%s" % classpath)

    def get_path(self, filename):
        """Return a path to filename that behaves as if original directory is current working directory

        This will internally convert relative paths to be relative to
        the original working directory (otherwise, NATS considers
        NATS_HOME to be the working directory).
        """
        if not os.path.isabs(filename):
            filename = os.path.join(self.cwd, filename)
        return filename

    def _stop_jvm(self):
        jpype.shutdownJVM()


NATS_HOME = os.environ.get('NATS_HOME')

def read_nats_output_file(filename):
    """Read the specified NATS output file

    Parameters
    ----------
    filename : str
        Input file to read

    Returns
    -------
    Single formatted data frame"""

    # Read all lines:
    with open(filename, 'r') as f:
        lines = f.readlines()

    # Read header information out of specific line numbers
    header_cols = lines[4].strip()[3:].split(',')
    data_cols = lines[5].strip()[3:].split(',')
    start_time = int(lines[7])

    # Store all lines after header
    lines = lines[9:]

    # Flag header lines, which may occur throughout the file
    is_header_line = [line.split(',')[0].isalpha() for line in lines]
    header_indices = np.where(is_header_line)[0]

    # Read in data by iterating over the header rows.  Each header row
    # specifies the number of records that follow.  That number is
    # used to find the corresponding subset of data lines associated
    # with the header, and those lines are read in as a DataFrame
    # according to the column names defined above.
    df = pd.DataFrame(columns=data_cols + ['callsign','origin','destination'])
    for header_idx in header_indices:
        header_row = pd.read_csv(StringIO(lines[header_idx]), header=None, names=header_cols).iloc[0]
        nrows = header_row['number_of_trajectory_rec']
        aircraft_df = pd.read_csv(StringIO('\n'.join(lines[header_idx+1:header_idx+1+nrows])), header=None, names=data_cols)
        # Fill in auxiliary data that comes from the header row
        aircraft_df['callsign'] = header_row['callsign']
        aircraft_df['origin'] = header_row['origin_airport']
        aircraft_df['destination'] = header_row['destination_airport']
        df = df.append(aircraft_df)


    df.rename(columns={'timestamp(UTC sec)':'time',
                       'course':'heading',
                       'rocd_fps':'rocd',
                       'sector_name':'sector',
                       'tas_knots':'tas',
                       'flight_phase':'status',
                       'altitude_ft':'altitude'},
              inplace=True)
    df['time'] += start_time
    df['time'] = pd.to_datetime(df['time'], unit='s')

    # Keep only selected columns
    selected_cols = ['time','callsign','origin','destination','latitude','longitude','altitude','rocd','tas','heading','sector','status']
    df = df[selected_cols]

    return df

def get_closest_node_at_airport(lat,lon,airport,domain=['Rwy','Gate','Txy','Ramp','Parking']):
    # Read node definition .csv file from NATS directory for given airport
    df = pd.read_csv(NATS_HOME+'/share/libairport_layout/Airport_Rwy/{}_Nodes_Def.csv'.format(airport))

    # Filter the nodes by the specified domain, default is all
    df = df.loc[df.domain.isin(domain)]

    # Compute distances between the node subset and the iff data lat/lon
    df['dists']=np.sqrt((df.lat-lat)**2+(df.lon-lon)**2)

    # Return node with the minimum distance
    return df.loc[df.dists.idxmin()]['id']

def get_list_of_adjacent_nodes(node,airport,domain=['Rwy','Txy','Ramp','Parking','Gate'], return_ordered=False):

    # Read node link .csv file from NATS directory for given airport
    df = pd.read_csv(NATS_HOME+'/share/libairport_layout/Airport_Rwy/{}_Nodes_Links.csv'.format(airport))

    # Filter dataframe by having the specified node in the
    # n1 or n2 column
    df = df.loc[(df['n1.id']==node) | (df['n2.id']==node)].copy()

    # Get list of all the adjacent nodes to the specified node
    adjacent_nodes = [nid for nid in df['n1.id'] if nid != node]+[nid for nid in df['n2.id'] if nid != node]
    adjacent_nodes = [node for node in adjacent_nodes if node.split('_')[0] in domain] 

    # If we want to return the nodes ordered by domain
    if return_ordered:
       adjacent_nodes = [node for node in adjacent_nodes for key in domain if key in node]
    return list(set(adjacent_nodes))

def get_adjacent_node_closer_to_runway(nodeList,runwayNode,airport):
    df = pd.read_csv(NATS_HOME+'/share/libairport_layout/Airport_Rwy/{}_Nodes_Def.csv'.format(airport))
    rwy_lat = df.loc[df['id']==runwayNode]['lat'].values[0]
    rwy_lon = df.loc[df['id']==runwayNode]['lon'].values[0]

    df = df.loc[df['id'].isin(nodeList)].copy()
    df['dists']=np.sqrt((df.lat-rwy_lat)**2+(df.lon-rwy_lon)**2)
    closest_node = df.loc[df.dists.idxmin()]['id']
    return closest_node

def get_shortest_taxi_route_from_A_to_B(nodeList,next_node,natsSim,airport):
    taxi_routes=dict()
    for node in nodeList:
        taxi_routes[node]=list(natsSim.airportInterface.get_taxi_route_from_A_To_B('default',airport,node,next_node))

    next_node,shortest_route = min(taxi_routes.items(), key = lambda x:len(x))
    return shortest_route
    
