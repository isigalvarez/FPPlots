# !usr/bin/env python3
# ===========================================================
# Created on 22/04/2019
# This script defines a class to handle FLEXPART runs.
#
# The script needs to install the f90nml package to write 
# fortran namelists, see:
# https://github.com/marshallward/f90nml
# ===========================================================

import os
import shutil
import errno
import subprocess
import f90nml

def main():
    # Define paths
    dirPath = '/home/isi/FLEXPART/flexpart10_git/Runs/FPRun_01/'
    flexpartPath = '/home/isi/FLEXPART/flexpart10_git/'
    meteoPath = '/home/isi/FLEXPART/Meteo/ECMWF/20170829_EA'
    runPath = flexpartPath+'src/FLEXPART'
    paths = (dirPath, flexpartPath, meteoPath)
    # ==  Create and prepare an instance of the class =====
    # Create the class
    FPRun = FlexpartRun(paths)
    # == Prepare the files for standard run ===============
    FPRun.write_COMMAND()
    params = [{'IDATE1': 20170831, 'ITIME1': 90000,
               'IDATE2': 20170831, 'ITIME2': 100000},
              {'IDATE1': 20170831, 'ITIME1': 110000,
               'IDATE2': 20170831, 'ITIME2': 120000}]
    FPRun.write_RELEASES(params)
    FPRun.write_OUTGRID()
    # == Run the simulation ===============================
    # FPRun.run()

def testing():
    # Define parameters
    flexpartPath = 'testData/flexpartdirectorySimulation/'
    dirPath = 'testData/flexpartConfigDirectory/'
    meteoPath = 'testData/meteoDirectorySimulation/'
    paths = (dirPath, flexpartPath, meteoPath)
    # ==  Create and prepare an instance of the class =====
    # Create the class (VERIFIED)
    FPRun = FlexpartRun(paths)
    # == Prepare the COMMAND file =========================
    # Try to print the COMMAND parameters (VERIFIED)
    FPRun.print_COMMAND()
    # Write the COMMAND with default options (VERIFIED)
    FPRun.write_COMMAND()
    FPRun.print_COMMAND()
    # Write the COMMAND with different options (VERIFIED)
    params = {'LDIRECT': 1}
    FPRun.write_COMMAND(params)
    FPRun.print_COMMAND()
    # == Prepare the RELEASES file =========================
    # Try to print the RELEASES parameters (VERIFIED)
    FPRun.print_RELEASES()
    # Write the RELEASES with default options (VERIFIED)
    FPRun.write_RELEASES()
    FPRun.print_RELEASES()
    # Write the RELEASES with different options (VERIFIED)
    params = [{'IDATE1': 20170831, 'ITIME1': 90000,
               'IDATE2': 20170831, 'ITIME2': 100000},
              {'IDATE1': 20170831, 'ITIME1': 110000,
               'IDATE2': 20170831, 'ITIME2': 120000}]
    FPRun.write_RELEASES(params)
    FPRun.print_RELEASES()
    # == Prepare the OUTGRID file =========================
    # Try to print the OUTGRID parameters (VERIFIED)
    FPRun.print_OUTGRID()
    # Write the OUTGRID with default options (VERIFIED)
    FPRun.write_OUTGRID()
    FPRun.print_OUTGRID()
    # Write the OUTGRID with different options (VERIFIED)
    params = {'OUTLON0': -90}
    FPRun.write_OUTGRID(params)
    FPRun.print_OUTGRID()


class FlexpartRun:
    """
    This is a class that initialize a FLEXPART run creating
    everything that will be need to correctly run simulation.
    """

    def __init__(self, paths):
        """
        Initialize parameters
        """
        # == Input parameters == #
        # Define directory path
        self.dirPath = os.path.abspath(paths[0])
        # Define directory where FLEXPART is installed
        self.flexpartPath = os.path.abspath(paths[1])
        # Define the meteo files directory
        self.meteoPath = os.path.abspath(paths[2])
        # == Empty parameters == #
        # Define COMMAND parameters
        self.command = {}
        # Define RELEASE parameters
        self.releases = []
        # Define OUTGRID parameters
        self.outgrid = {}
        # == Derived parameters == #
        # options ans output dirs and pathnames file location
        self.optionsPath = os.path.abspath(self.dirPath+'/options/')
        self.outputPath = os.path.abspath(self.dirPath+'/output/')
        self.pathnamesPath = os.path.abspath(self.dirPath+'/pathnames')
        # COMMAND, RELEASES and OUTGRID file location
        self.commandPath = os.path.abspath(self.optionsPath+'/COMMAND')
        self.releasesPath = os.path.abspath(self.optionsPath+'/RELEASES')
        self.outgridPath = os.path.abspath(self.optionsPath+'/OUTGRID')
        # FLEPART executable location
        self.runFlexpart = os.path.abspath(self.flexpartPath+'/src/FLEXPART')
        # == Prepare simulation directory tree == #
        self.prepareFiles()

    def prepareFiles(self):
        """
        This method creates the 'option', 'output' and the
        rest of the files needed to host a Flexpart run.
        """
        # Create a new directory on dirPath
        if not os.path.exists(self.dirPath):
            os.makedirs(self.dirPath)
        # Copy the 'options' directory form 'flexpartPath'
        try:
            shutil.copytree(self.flexpartPath+'/options',
                            self.optionsPath)
        except OSError as e:
            # If the error was caused because the source wasn't a directory
            if e.errno == errno.ENOTDIR:
                shutil.copy(self.flexpartPath+'/options/',
                            self.optionsPath)
            else:
                print(f'Directory not copied. Error: {e}')
        # Create the output directory
        if not os.path.exists(self.dirPath+'/output'):
            os.makedirs(self.outputPath)
        # Create the pathnames
        with open(f'{self.pathnamesPath}', 'w+', newline='\r\n') as f:
            # Write the locations
            f.write(f'{self.optionsPath}/ \n')
            f.write(f'{self.outputPath}/ \n')
            f.write(f'{self.meteoPath}/ \n')
            # Define the AVAILABLE path and write it
            availablePath = os.path.abspath(f'{self.meteoPath}/AVAILABLE')
            f.write(f'{availablePath} \n')

    def write_COMMAND(self, params={}):
        """
        This method rewrites the COMMAND file to
        configure the simulation
        """
        # Define defaults
        self.command = {'LDIRECT': -1,
                        'IBDATE': 20170829, 'IBTIME': 000000,
                        'IEDATE': 20170831, 'IETIME': 230000,
                        'LOUTSTEP': 300, 'LOUTAVER': 300,
                        'LOUTSAMPLE': 100, 'ITSPLIT': 99999999, 
                        'LSYNCTIME': 100, 'CTL': -5.00000000,
                        'IFINE': 4, 'IOUT': 13, 'IPOUT': 1,
                        'LSUBGRID': 0, 'LCONVECTION': 1, 'LAGESPECTRA': 0,
                        'IPIN': 0, 'IOUTPUTFOREACHRELEASE': 1, 'IFLUX': 0,
                        'MDOMAINFILL': 0, 'IND_SOURCE': 1, 'IND_RECEPTOR': 1,
                        'MQUASILAG': 0, 'NESTED_OUTPUT': 0, 'LINIT_COND': 0,
                        'SURF_ONLY': 0, 'CBLFLAG': 0,
                        'OHFIELDS_PATH': '../../flexin/'}
        # Redefined the given params
        for key in params.keys():
            self.command[key] = params[key]
        # Create a copy of the existing COMMAND filename
        shutil.copy(self.commandPath,self.commandPath+'.original')
        # Open a namelsit with f90nml
        nml = f90nml.read(self.commandPath+'.original')
        # Iterate over command and write the change
        for key in self.command.keys():
            nml['COMMAND'][key] = self.command[key]
        nml.write(self.commandPath+'_temp')
        os.replace(self.commandPath+'_temp',self.commandPath)      

    def print_COMMAND(self):
        """
        This method prints the current configuration written
        in the COMMAND file
        """
        # Check if there is any parameters defined
        if len(self.command) == 0:
            print('No COMMAND parameters have been defined yet.')
        else:
            # Initial statment
            print('Content of COMMAND File:')
            # Iterate over keys
            for key in self.command:
                print(f' {key} = {self.command[key]}')

    def write_RELEASES(self, params=[{}]):
        """
        This method rewrites the RELEASES file to
        configure the simulation
        """
        # Define defaults
        default_params = {'IDATE1': '20170831', 'ITIME1': '095900',
                          'IDATE2': '20170831', 'ITIME2': '100000',
                          'LON1': '-22.981', 'LON2': '-22.952',
                          'LAT1': '16.786', 'LAT2': '16.787',
                          'Z1': '833.51', 'Z2': '833.52',
                          'ZKIND': '1', 'MASS': '100000000.0',
                          'PARTS': '10000', 'COMMENT': '"RELEASE 1"'}
        # Initialize the list of releases
        self.releases = []
        # Iterate over params changing what's asked
        for i, param in enumerate(params):
            # Create a copy of default options
            release = default_params.copy()
            # Iterate over paramaters to be changed
            for key in param.keys():
                # Change the value
                release[key] = param[key]
            # Append the release to internal value
            self.releases.append(release)
        # Change the existing COMMAND filename
        os.replace(self.optionsPath+'/RELEASES',
                   self.optionsPath+'/RELEASES.original')
        # Open the new COMMAND file
        with open(self.optionsPath+'/RELEASES', 'w+', newline='') as f:
            # Write the lines of &RELEASES_CTRL
            f.write('&RELEASES_CTRL \n')
            f.write(f' NSPEC =1, \n')
            f.write(f' SPECNUM_REL = 24, \n')
            f.write(' / \n')
            # Iterate over each release
            for release in self.releases:
                # Write the first line of &RELEASES
                f.write('&RELEASE \n')
                # Write the lines in params
                for key in release.keys():
                    f.write(f' {key}= {release[key]}, \n')
                # Write the final line
                f.write(' / \n')

    def print_RELEASES(self):
        """
        This method prints the current configuration written
        in the RELEASE file
        """
        # Check if there is any parameters defined
        if len(self.releases) == 0:
            print('No RELEASES parameters have been defined yet.')
        else:
            # Iterate over all releases
            for i, release in enumerate(self.releases):
                print(f'Parameters for release {i+1}')
                # Iterate over every paramter
                for key in release:
                    print(f' {key} = {release[key]}')

    def write_OUTGRID(self, params={}):
        """
        This method rewrites the OUTGRID file to
        configure the simulation
        """
        # Define defaults
        self.outgrid = {'OUTLON0': -80.0, 'OUTLAT0': -35.0,
                        'NUMXGRID': 130, 'NUMYGRID': 100,
                        'DXOUT': 1.0, 'DYOUT': 1.0,
                        'OUTHEIGHTS': [100.0, 500.0, 1000.0, 50000.0]}
        # Redefined the given params
        for key in params.keys():
            self.outgrid[key] = params[key]
        # Create a copy of the existing OUTGRID filename
        shutil.copy(self.outgridPath,self.outgridPath+'.original')
        # Open a namelsit with f90nml
        nml = f90nml.read(self.outgridPath+'.original')
        # Iterate over command and write the change
        for key in self.outgrid.keys():
            nml['OUTGRID'][key] = self.outgrid[key]
        nml.write(self.outgridPath+'_temp')
        os.replace(self.outgridPath+'_temp',self.outgridPath)   
            
    def print_OUTGRID(self):
        """
        This method prints the current configuration written
        in the OUTGRID file
        """
        # Check if there is any parameters defined
        if len(self.outgrid) == 0:
            print('No OUTGRID parameters have been defined yet.')
        else:
            # Initial statment
            print('Content of OUTGRID File:')
            # Iterate over keys
            for key in self.outgrid:
                print(f' {key} = {self.outgrid[key]}')

    def run(self):
        """
        This method moves to the run directory and launches the
        FLEXPART simulation
        """
        # Move to the directory
        os.chdir(self.dirPath)
        # Call FLEXPART
        print('Running simulation...')
        a = subprocess.call(self.runFlexpart,shell=True)
        print('   Done.')
        return a

if __name__ == '__main__':
    print('Ready to go!\n')
    # testing()
    main()