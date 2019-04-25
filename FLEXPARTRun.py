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
import pandas as pd
from numpy import floor


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
        # FLEPART executable location and AVAILABLE path
        self.runFlexpart = os.path.abspath(self.flexpartPath+'/src/FLEXPART')
        self.availablePath = os.path.abspath(f'{self.meteoPath}/AVAILABLE')
        # == Prepare simulation directory tree == #
        self.prepareFiles()

    def prepareFiles(self):
        """
        Creates the 'option', 'output' and the rest of the files 
        needed to host a Flexpart run.
        """
        # Show a message
        print('\nPreparing FLEXPART environment...')
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
            f.write(f'{self.availablePath} \n')
        # Make sure that the AVAILABLE file exists within meteoPath
        if not os.path.isfile(self.availablePath):
            print('\n (!) WARNING (!)')
            print('Please copy the AVAILABLE file into the meteo directory:')
            print(f' {self.meteoPath}/')

    def write_COMMAND(self, params={}):
        """
        Rewrites the COMMAND file to configure the simulation.
        """
        # Define defaults
        self.command = {'LDIRECT': -1,
                        'IBDATE': 20170829, 'IBTIME': 100000,
                        'IEDATE': 20170831, 'IETIME': 110000,
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
        shutil.copy(self.commandPath, self.commandPath+'.original')
        # Open a namelsit with f90nml
        nml = f90nml.read(self.commandPath+'.original')
        # Iterate over command and write the change
        for key in self.command.keys():
            nml['COMMAND'][key] = self.command[key]
        nml.write(self.commandPath+'_temp')
        os.replace(self.commandPath+'_temp', self.commandPath)

    def print_COMMAND(self):
        """
        Prints the current configuration written in the COMMAND file.
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
        Rewrites the RELEASES file to configure the simulation.
        """
        # Define defaults
        default_params = {'IDATE1': '20170831', 'ITIME1': '095900',
                          'IDATE2': '20170831', 'ITIME2': '100000',
                          'LON1': '-22.981', 'LON2': '-22.952',
                          'LAT1': '16.786', 'LAT2': '16.787',
                          'Z1': '833.51', 'Z2': '833.52',
                          'ZKIND': '1', 'MASS': '100000000.0',
                          'PARTS': '10000', 'COMMENT': '"RELEASE 1"'}
        # Initialize releases
        releases = []
        # Iterate over params changing what's asked
        for param in params:
            # Create a copy of default options
            release = default_params.copy()
            # Iterate over paramaters to be changed
            for key in param.keys():
                # Change the value
                release[key] = param[key]
            # Append the release
            releases.append(release)
        # Save a copy to the internal value
        self.releases = releases[:]
        # Change the existing COMMAND filename
        os.replace(self.optionsPath+'/RELEASES',
                   self.optionsPath+'/RELEASES.original')
        # Open the new COMMAND file
        with open(self.optionsPath+'/RELEASES', 'w+', newline='\n') as f:
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
        Prints the current configuration written in the RELEASE file.
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
        Rewrites the OUTGRID file to configure the simulation.
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
        shutil.copy(self.outgridPath, self.outgridPath+'.original')
        # Open a namelsit with f90nml
        nml = f90nml.read(self.outgridPath+'.original')
        # Iterate over command and write the change
        for key in self.outgrid.keys():
            nml['OUTGRID'][key] = self.outgrid[key]
        nml.write(self.outgridPath+'_temp')
        os.replace(self.outgridPath+'_temp', self.outgridPath)

    def print_OUTGRID(self):
        """
        Prints the current configuration written in the OUTGRID file.
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

    def prepare_Run(self):
        """
        Creates a link to the FLEXPART executable in the simulation 
        directory, laying the grund to easily perform the simulation.
        """
        # Try to reate the link
        try:
            os.symlink(f'{self.flexpartPath}/src/FLEXPART',
                       f'{self.dirPath}/FLEXPART')
            # Show message
            print(
                f'\nSimulation hosted in: \n   {self.dirPath}\nis ready to go.')
        except FileExistsError:
            print('\nFLEXPART link already exists. Check directory tree.')

    def change_particlesNumber(self, number=1000):
        """
        Rewrite the RELEASES file to change the number of particles 
        for each release.
        """
        # If a number is provided, go on
        if number:
            # Extract previous release parameters
            releases = self.releases[:]
            # Redefine PARTS
            for release in releases:
                release['PARTS'] = number
            # Reassing
            self.write_RELEASES(releases)

    def check_totalParticles(self,maxpart=100000):
        """
        Checks the total number of particles that will
        be released. This number should not exceed 100 000.

        This method returns 'None' if the number is ok or a suggested
        number if there are too many particles
        """
        # Initialize the number
        n_particles = 0
        # Iterate over releases
        for release in self.releases:
            # Add the particles
            n_particles += int(release['PARTS'])
        # Print the number and give a warning if needed
        print('\nChecking releases...')
        print(f' Total number of releases: {len(self.releases)}')
        print(f' Average particles per release: {n_particles/len(self.releases)}')
        print(f' Total number of particles released: {n_particles}')
        # Check the number
        if n_particles >= maxpart:
            print(f'\n (!) WARNING (!)')
            print(('The number of particles exceeds the maximum allowed '
                   + f'({maxpart}). Consider reducing the number '
                   + 'of releases or the number of particles for each '
                   + 'release.'))
            print(('Please ignore this message if the maximum number of '
                   + 'particles (maxpart) was changed in the file '
                   + '"par_mod.f90" before FLEXPART compilation.'))
            # Calculate an appropiate number and return it
            return int(floor(maxpart/len(self.releases)))
        else:
            return None

    def check_meteoRange(self):
        """
        Checks that the meteorological files available will be enough
        to encompass the whole simulation.
        """
        # Open the AVAILABLE file
        df = pd.read_csv(f'{self.availablePath}', skiprows=3,
                         sep='\s+', dtype='str', header=None,
                         usecols=[0, 1])
        # Create the date
        date_meteo = pd.to_datetime(df[0]+df[1])
        # Extract the meteo limits
        firstDate_meteo = date_meteo.min()
        lastDate_meteo = date_meteo.max()
        # Extract the date from the COMMAND parameters
        date = f'{self.command["IBDATE"]}'.zfill(6)
        hour = f'{self.command["IBTIME"]}'.zfill(6)
        firstDate_command = pd.to_datetime(date+hour)
        date = f'{self.command["IEDATE"]}'.zfill(6)
        hour = f'{self.command["IETIME"]}'.zfill(6)
        lastDate_command = pd.to_datetime(date+hour)
        # Check initial dates
        print('\nChecking initial dates...')
        if firstDate_meteo < firstDate_command:
            print(' Initial dates are correct.')
        else:
            print(' Inconsistent dates. Check simulation parameters.')
            print(f'  First meteo date: {firstDate_meteo}')
            print(f'  First simulation date: {firstDate_command}')
        # Check final dates
        print('Checking final dates...')
        if lastDate_meteo > lastDate_command:
            print(' Final dates are correct.')
        else:
            print(' Inconsistent dates. Check simulation parameters.')
            print(f'  Last meteo date: {lastDate_meteo}')
            print(f'  Last simulation date: {lastDate_command}')


def testing():
    # Define parameters
    runDir = '/home/isi/FLEXPART/flexpart10_git/Runs/FPRun_01/'
    flexpartDir = '/home/isi/FLEXPART/flexpart10_git/'
    meteoDir = '/home/isi/FLEXPART/Meteo/ECMWF/20170829_EA'
    paths = (runDir, flexpartDir, meteoDir)
    # ==  Create and prepare an instance of the class =====
    # Create the class (VERIFIED)
    FPRun = FlexpartRun(paths)
    # == Prepare the COMMAND file =========================
    print('\n# == Prepare the COMMAND file =========================')
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
    print('\n# == Prepare the RELEASES file =========================')
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
    print('\n# == Prepare the OUTGRID file =========================')
    # Try to print the OUTGRID parameters (VERIFIED)
    FPRun.print_OUTGRID()
    # Write the OUTGRID with default options (VERIFIED)
    FPRun.write_OUTGRID()
    FPRun.print_OUTGRID()
    # Write the OUTGRID with different options (VERIFIED)
    params = {'OUTLON0': -90}
    FPRun.write_OUTGRID(params)
    FPRun.print_OUTGRID()
    # == Check the number of particles ===================
    print('\n# == Check the number of particles ===================')
    n_particles = FPRun.check_totalParticles()
    FPRun.change_particlesNumber(n_particles)
    FPRun.print_RELEASES()
    # == Check meteo =====================================
    print('\n# == Check meteo =====================================')
    FPRun.command
    FPRun.check_meteoRange()


if __name__ == '__main__':
    print('Ready to go!\n')
    testing()
