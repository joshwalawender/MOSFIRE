import re
from datetime import datetime as dt
from time import sleep
import logging

# Wrap ktl import in try/except so that we can maintain test case or simulator
# version of functions.
try:
    import ktl
    from ktl import Exceptions as ktlExceptions
except ModuleNotFoundError:
    ktl = None

from .Instruments import AbstractInstrument


# -----------------------------------------------------------------------------
# HIRES
# -----------------------------------------------------------------------------
class HIRES(AbstractInstrument):
    def __init__(self):
        super().__init__()
        self.name = 'HIRES'
        self.optical = True
        self.allowed_sampmodes = [1]
        self.scripts = ["stare", "slit nod", "ABBA", "ABB'A'"]
        self.binnings = ["1x1", "1x2", "2x1", "2x2", "3x1"]
        self.basename = f"h{dt.utcnow().strftime('%Y%m%d')}_"
        self.serviceNames = ["hires", "hiccd", "expo"]
        self.obstypes = ['Object', 'Dark', 'Line', 'Bias', 'IntFlat', 'DmFlat',
                         'SkyFlat']
        self.slits = {'B1': (3.5, 0.574),
                      'B2': (7.0, 0.574),
                      'B3': (14.0, 0.574),
                      'B4': (28.0, 0.574),
                      'B5': (3.5, 0.861),
                      'C1': (7.0, 0.861),
                      'C2': (14.0, 0.861),
                      'C3': (28.0, 0.861),
                      'C4': (3.5, 1.148),
                      'C5': (7.0, 1.148),
                      'D1': (14.0, 1.148),
                      'D2': (28.0, 1.148),
                      'D3': (7.0, 1.722),
                      'D4': (14.0, 1.722),
                      'D5': (0.119, 0.179),
                      'E1': (1.0, 0.4),
                      'E2': (3.0, 0.4),
                      'E3': (5.0, 0.4),
                      'E4': (7.0, 0.4),
                      'E5': (1.0, 0.8),
                      }


        #----------------------------------------------------------------------
        # Create logger object
        #----------------------------------------------------------------------
        self.log = logging.getLogger('HIRES')
        self.log.setLevel(logging.DEBUG)
        ## Set up console output
        LogConsoleHandler = logging.StreamHandler()
        LogConsoleHandler.setLevel(logging.DEBUG)
        LogFormat = logging.Formatter('%(asctime)s %(levelname)8s: %(message)s',
                                      datefmt='%Y-%m-%d %H:%M:%S')
        LogConsoleHandler.setFormatter(LogFormat)
        self.log.addHandler(LogConsoleHandler)
        ## Set up file output
#         LogFileName = None
#         LogFileHandler = logging.FileHandler(LogFileName)
#         LogFileHandler.setLevel(logging.DEBUG)
#         LogFileHandler.setFormatter(LogFormat)
#         self.log.addHandler(LogFileHandler)

        #----------------------------------------------------------------------
        # Connect to keyword services
        #----------------------------------------------------------------------
        self.connect()


    def get_collimator(self):
        '''Determine which collimator is in the beam.  Returns a string of
        'red' or 'blue' indicating which is in beam.  Returns None if it can
        not interpret the result.
        '''
        if self.services is None:
            return None
        self.log.debug('Getting current collimator ...')
        collred = self.services['hires']['COLLRED'].read()
        collblue = self.services['hires']['COLLBLUE'].read()
        if collred == 'red' and collblue == 'not blue':
            collimator = 'red'
        elif collred == 'not red' and collblue == 'blue':
            collimator = 'blue'
        else:
            collimator = None
        self.log.debug(f'  collimator = {collimator}')
        return collimator

    def lights_are_on(self):
        '''Returns True if lights are on in the enclosure.
        '''
        if self.services is None:
            return None
        self.log.debug('Getting status of enclosure lights ...')
        lights_str = self.services['hires']['lights'].read()
        lights = (lights_str == 'on')
        self.log.debug(f'  lights are {lights_str}')
        return lights

    def get_iodine_temps(self):
        '''Returns the iodine cell temperatures (tempiod1, tempiod2) in units
        of degrees C.
        '''
        if self.services is None:
            return None
        self.log.debug('Getting iodine cell temperatures ...')
        tempiod1 = float(self.services['hires']['tempiod1'].read())
        tempiod2 = float(self.services['hires']['tempiod2'].read())
        self.log.debug(f'  tempiod1 = {tempiod1}')
        self.log.debug(f'  tempiod2 = {tempiod2}')
        return [tempiod1, tempiod2]

    def check_iodine_temps(self, target1=65, target2=50, range=0.1, wait=False):
        '''Checks the iodine cell temperatures agains the given targets and
        range.  Default values are those used by the CPS team.
        '''
        if self.services is None:
            return None
        self.log.debug('Checking whether iodine cell is at operating temp ...')
        tempiod1, tempiod2 = self.get_iodine_temps()
        tempiod1_diff = tempiod1 - target1
        tempiod2_diff = tempiod2 - target2
        self.log.debug(f'  tempiod1 is {tempiod1_diff:.1f} off nominal')
        self.log.debug(f'  tempiod2 is {tempiod2_diff:.1f} off nominal')
        if abs(tempiod1_diff) < range and abs(tempiod2_diff) < range:
            self.log.debug('  Iodine temperatures in range')
            return True
        else:
            self.log.debug('  Iodine temperatures NOT in range')
            if wait is True:
                self.log.info('  Waiting 10 minutes for iodine cell to reach '
                              'temperature')
                done = ktl.waitFor(f'($hires.TEMPIOD1 > {target1-range}) and '\
                                   f'($hires.TEMPIOD1 < {target1+range}) and '\
                                   f'($hires.TEMPIOD2 > {target2-range}) and '\
                                   f'($hires.TEMPIOD2 < {target2+range})',\
                                   timeout=600)
                if done is False:
                    self.logger.warning('Iodine cell did not reach temperature'
                                        'within 10 minutes')
                return done
            else:
                return False

    def get_binning(self):
        '''Populates the binning property and return the value.  Both are a
        tuple of (binX, binY).
        '''
        if self.services is None:
            self.log.warning('Not connected to instrument.')
            return None
        self.log.debug('Getting binning status ...')
        keywordresult = self.services['hiccd']['BINNING'].read()
        binningmatch = re.match('\\n\\tXbinning (\d)\\n\\tYbinning (\d)',
                                keywordresult)
        if binningmatch is not None:
            self.binning = (int(binningmatch.group(1)),
                            int(binningmatch.group(2)))
            self.log.debug(f'  binning = {self.binning}')
            return self.binning
        else:
            self.log.error(f'Could not parse keyword value "{keywordresult}"')
            return None


    def get_window(self):
        '''
        '''
        if self.services is None:
            self.log.warning('Not connected to instrument.')
            return None
        self.log.debug('Getting windowing status ...')
        keywordresult = self.services['hiccd']['WINDOW'].read()
        winmatch = re.match('\\n\\tchip number (\d)\\n\\txstart (\d+)\\n\\t'
                            'ystart (\d+)\\n\\txlen (\d+)\\n\\tylen (\d+)',
                                keywordresult)
        if winmatch is not None:
            self.window = (int(winmatch.group(1)),
                           int(winmatch.group(2)),
                           int(winmatch.group(3)),
                           int(winmatch.group(4)),
                           int(winmatch.group(5)),
                          )
            self.log.debug(f'  window = {self.window}')
            return self.window
        else:
            self.log.error(f'Could not parse keyword value "{keywordresult}"')
            return None


    def get_gain(self):
        '''Return the gain as a string 'low' or 'high'.
        '''
        if self.services is None:
            self.log.warning('Not connected to instrument.')
            return None
        self.log.debug('Getting gain ...')
        gain = self.services['hiccd']['CCDGAIN'].read()
        return gain


    def get_ccdspeed(self):
        '''Return the CCD readout speed as a string.
        '''
        if self.services is None:
            self.log.warning('Not connected to instrument.')
            return None
        self.log.debug('Getting CCDSPEED ...')
        speed = self.services['hiccd']['CCDSPEED'].read()
        return speed


    def _set_binning(self, binX, binY):
        '''Private method called by the set_binning method of the
        AbstractInstrument class.  That method should be used by users, this
        method captures the exact keyword commands to change binning for each
        specific instrument.
        '''
        self.log.debug(f'Setting binning to {(binX, binY)}')
        if self.services is not None:
            self.services['hiccd']['BINNING'].write((binX, binY))
            self.get_binning()
        else:
            self.log.warning('Not connected to instrument.')
            self.binning = (binX, binY)

        if (binX, binY) == self.get_binning():
            self.log.debug('  Done')
        else:
            self.log.error('  Failed to set binning')
            self.log.error(f'  Desired: ({binX}, {binY})')
            self.log.error(f'  Result: {self.get_binning()}')

    def _set_itime(self, itime):
        if self.services is not None:
            self.services['hiccd']['TTIME'].write(itime)
        else:
            self.log.warning('Not connected to instrument.')

    def take_exposure(self, n=1):
        images = []
        busy = bool(self.services['hiccd']['OBSERVIP'].read())
        if busy is True:
            self.info('Waiting 5 minutes for current observation to finish')
            busy = not ktl.waitFor('($hiccd.OBSERVIP == false)', timeout=300)

#         for i in range(0,n):
#             ## Check output file name
#             outfile_base = self.get('OUTFILE')
#             outfile_seq = int(self.get('FRAMENO'))
#             outfile_name = '{}{:04d}.fits'.format(outfile_base, outfile_seq)
#             outfile_path = self.get('OUTDIR')
#             outfile = os.path.join(outfile_path, outfile_name)
#             if os.path.exists(outfile):
#                 self.warning('{} already exists'.format(outfile_name))
#                 self.warning('System will copy old file to {}.old'.format(outfile_name))
#             ## Begin Exposure
#             self.info('Exposing ({:d} of {:d}) ...'.format(i+1, n))
#             exptime = float(self.get('TTIME'))
#             self.info('  Exposure Time = {:.1f} s'.format(exptime))
#             self.info('  Object = "{}"'.format(self.get('OBJECT')))
#             self.info('  Type = "{}"'.format(self.get('OBSTYPE')))
#             tick = time.now()
#             tock = time.now()
#             elapsed = (tock-tick).total_seconds()
#             self.debug('  {:.1f}s: {}'.format(elapsed, 'Erasing CCD'))
#             done = ktl.Expression('($hiccd.OBSERVIP == false) and ($hiccd.WDISK == false)')
#             self.set('EXPOSE', True)
#             while not done.evaluate():
#                 self.print_state_change(tick=tick)
#                 sleep(0.1)
#             sleep(1.0) # time shim :(
#             tock = time.now()
#             elapsed = (tock-tick).total_seconds()
#             self.info('  File will be written to: {}'.format(outfile))
#             images.append(outfile)
#             self.info('  Done ({:.1f} s elapsed)'.format(elapsed))
#     return images

    def get_DWRN2LV(self):
        '''Returns a float of the current camera dewar level, supposedly in
        percentage, but as this is poorly calibrated, it maxes out at nearly
        120% as of mid 2018.
        '''
        if self.services is None:
            return None
        self.log.debug('Getting camera dewar level ...')
        DWRN2LV = float(self.services['hiccd']['DWRN2LV'].read())
        self.log.debug(f'  DWRN2LV = {DWRN2LV:.1f}')
        return DWRN2LV

    def estimate_dewar_time(self):
        '''Estimate time remaining on the camera dewar.
        '''
        DWRN2LV = self.get_DWRN2LV()
        self.log.debug('Estimating camera dewar hold time ...')
        if DWRN2LV > 70:
            hold_time = '>12 hours'
        elif DWRN2LV > 10:
            hold_time = f"~{(DWRN2LV-10)/5:.1f} hours"
        else:
            self.log.warning(f'Dewar at {DWRN2LV:.1f} %. Fill immediately!')
            hold_time = 'WARNING!  Dewar level Low.  Fill immediately!'
        self.log.debug(f'  hold time: {hold_time}')
        return hold_time

    def get_RESN2LV(self):
        '''Returns a float of the current reserve dewar level.  Each camera
        dewar fill takes roughly 10% of the reserve dewar.
        '''
        if self.services is None:
            return None
        self.log.debug('Getting reserve dewar level ...')
        RESN2LV = float(self.services['hiccd']['RESN2LV'].read())
        self.log.debug(f'  RESN2LV = {RESN2LV:.1f}')
        return RESN2LV

    def fill_dewar(self):
        '''Fill camera dewar using procedure in /local/home/hireseng/bin/filln2
        '''
        if self.services is None:
            return None
        self.log.debug('Initiating dewar fill ...')
        if self.services['hiccd']['WCRATE'].read() is not False:
            self.log.warning('The CCD is currently reading out. '
                             'Try again when complete.')
            return None
        self.services['hiccd']['utbn2fil'].write('on')
        while self.services['hiccd']['utbn2fil'].read() != 'off':
            sleep(15)
        self.log.debug('  HIRES Dewar Fill is Complete.')
        return True

    def open_covers(self, wait=True):
        '''Opens all internal covers.
        
        Use same process as: /local/home/hires/bin/open.red and open.blue

        modify -s hires rcocover = open \
                        echcover = open   xdcover  = open \
                        co1cover = open   co2cover = open \
                        camcover = open   darkslid = open     wait

        modify -s hires bcocover = open \
                        echcover = open   xdcover  = open \
                        co1cover = open   co2cover = open \
                        camcover = open   darkslid = open     wait
        '''
        if self.services is None:
            return None
        collimator = self.get_collimator()
        self.log.debug(f'Opening {collimator} covers ...')

        if collimator == 'red':
            self.services['hires']['rcocover'].write('open', wait=False)
        elif collimator == 'blue':
            self.services['hires']['bcocover'].write('open', wait=False)
        else:
            self.log.error('Collimator is unknown. Cover not opened.')
        self.services['hires']['echcover'].write('open', wait=False)
        self.services['hires']['co1cover'].write('open', wait=False)
        self.services['hires']['xdcover'].write('open', wait=False)
        self.services['hires']['co2cover'].write('open', wait=False)
        self.services['hires']['camcover'].write('open', wait=False)
        self.services['hires']['darkslid'].write('open', wait=False)

        if wait is True:
            if collimator == 'red':
                self.services['hires']['rcocover'].write('open', wait=True)
            elif collimator == 'blue':
                self.services['hires']['bcocover'].write('open', wait=True)
            else:
                self.log.error('Collimator is unknown. Cover not opened.')
            self.services['hires']['echcover'].write('open', wait=True)
            self.services['hires']['co1cover'].write('open', wait=True)
            self.services['hires']['xdcover'].write('open', wait=True)
            self.services['hires']['co2cover'].write('open', wait=True)
            self.services['hires']['camcover'].write('open', wait=True)
            self.services['hires']['darkslid'].write('open', wait=True)
            self.log.debug('  Done.')

    def close_covers(self, wait=True):
        '''Closes all internal covers.
        '''
        if self.services is None:
            return None
        collimator = self.get_collimator()
        self.log.debug(f'Closing {collimator} covers ...')

        if collimator == 'red':
            self.services['hires']['rcocover'].write('closed', wait=False)
        elif collimator == 'blue':
            self.services['hires']['bcocover'].write('closed', wait=False)
        else:
            self.log.error('Collimator is unknown. Cover not closed.')
        self.services['hires']['echcover'].write('closed', wait=False)
        self.services['hires']['co1cover'].write('closed', wait=False)
        self.services['hires']['xdcover'].write('closed', wait=False)
        self.services['hires']['co2cover'].write('closed', wait=False)
        self.services['hires']['camcover'].write('closed', wait=False)
        self.services['hires']['darkslid'].write('closed', wait=False)

        if wait is True:
            if collimator == 'red':
                self.services['hires']['rcocover'].write('closed', wait=True)
            elif collimator == 'blue':
                self.services['hires']['bcocover'].write('closed', wait=True)
            else:
                self.log.error('Collimator is unknown. Cover not closed.')
            self.services['hires']['echcover'].write('closed', wait=True)
            self.services['hires']['co1cover'].write('closed', wait=True)
            self.services['hires']['xdcover'].write('closed', wait=True)
            self.services['hires']['co2cover'].write('closed', wait=True)
            self.services['hires']['camcover'].write('closed', wait=True)
            self.services['hires']['darkslid'].write('closed', wait=True)
            self.log.debug('  Done.')

    def iodine_start(self):
        '''Starts the iodine cell heater.  Cell takes ~45 minutes to warm up.
        
        Use same process as in /local/home/hires/bin/iod_start

        modify -s hires moniodt=1
        modify -s hires setiodt=50.
        modify -s hires iodheat=on
        '''
        if self.services is None:
            return None
        self.log.debug('Starting iodine heater')
        self.services['hires']['moniodt'].write(1)
        self.services['hires']['setiodt'].write(50)
        self.services['hires']['iodheat'].write('on')

    def iodine_stop(self):
        '''Turns off the iodine cell heater.
        
        Use same process as in /local/home/hires/bin/iod_stop

        modify -s hires moniodt=0
        modify -s hires iodheat=off
        '''
        if self.services is None:
            return None
        self.log.debug('Stopping iodine heater')
        self.services['hires']['moniodt'].write(0)
        self.services['hires']['iodheat'].write('off')

    def iodine_in(self, wait=True):
        self.log.debug('Inserting iodine cell')
        self.services['hires']['IODCELL'].write('in', wait=wait)

    def iodine_out(self, wait=True):
        self.log.debug('Removing iodine cell')
        self.services['hires']['IODCELL'].write('out', wait=wait)

    def open_slit(self, wait=True):
        '''Open the slit jaws.
        '''
        if self.services is None:
            return None
        self.log.debug('Setting an open slit (decker)')
        self.services['hires']['slitname'].write('opened', wait=wait)

    def set_decker(self, deckname, wait=True):
        '''Set the deckname keyword.  This method does not change any other
        configuration values.
        '''
        if self.services is None:
            return None
        assert deckname in self.slits.keys()
        slitdims = self.slits[deckname]
        self.log.debug(f'Setting decker to slit {deckname} '
                        '({slitdims[0]} x {slitdims[1]})')
        self.services['hires']['deckname'].write(deckname, wait=wait)

    def set_slit(self, deckname, wait=True):
        self.set_decker(deckname, wait=wait)

    def set_filters(self, fil1name, fil2name, wait=True):
        '''Set the filter wheels.
        '''
        if self.services is None:
            return None
        self.log.debug(f'Setting filters to {fil1name}, {fil2name}')
        self.services['hires']['fil1name'].write(fil1name, wait=wait)
        self.services['hires']['fil2name'].write(fil2name, wait=wait)

    def set_cafraw(self, cafraw, wait=True):
        if self.services is None:
            return None
        self.services['hires']['cafraw'].write(cafraw, wait=wait)

    def set_cofraw(self, cofraw, wait=True):
        if self.services is None:
            return None
        self.services['hires']['cofraw'].write(cafraw, wait=wait)

    def set_tvfilter(self, tvf1name, wait=True):
        if self.services is None:
            return None
        self.services['hires']['TVF1NAME'].write(tvf1name, wait=wait)

    def get_obstype(self):
        if self.services is None:
            return None
        obstype = self.services['hiccd']['obstype'].read()
        assert obstype in self.obstypes
        return obstype

    def set_obstype(self, obstype):
        if self.services is None:
            return None
        if obstype in self.obstypes:
            self.services['hiccd']['obstype'].write(obstype)
            return self.get_obstype()
        else:
            self.log.warning(f'OBSTYPE {obstype} not recognized.')
            self.log.warning(f'Allowed obstypes:')
            for otype in self.obstypes:
                self.log.warning(f'  {otype}')

    def take_exposure(self, obstype=None, exptime=None, nexp=1):
        '''Takes one or more exposures of the given exposure time and type.
        Modeled after goi script.
        '''
        if self.services is None:
            return None

        if obstype is None:
            obstype = self.services['hiccd']['OBSTYPE'].read()

        if obstype.lower() not in self.obstypes:
            print(f'OBSTYPE "{obstype} not understood"')
            return

        if self.services['hiccd']['OBSERVIP'].read() == 'true':
            print('Waiting up to 300s for current observation to finish')
            if not ktl.waitFor('($hiccd.OBSERVIP == False )', timeout=300):
                raise Exception('Timed out waiting for OBSERVIP')

        if exptime is not None:
            self.services['hiccd']['TTIME'].write(int(exptime))

        if obstype.lower() in ["dark", "bias", "zero"]:
            self.services['hiccd']['AUTOSHUT'].write(False)
        else:
            self.services['hiccd']['AUTOSHUT'].write(True)

        for i in range(nexp):
            exptime = int(self.services['hiccd']['TTIME'].read())
            print(f"Taking exposure {i:d} of {nexp:d}")
            print(f"  Exposure Time = {exptime:d} s")
            self.services['hiccd']['EXPOSE'].write(True)
            exposing = ktl.Expression("($hiccd.OBSERVIP == True) "
                                      "and ($hiccd.EXPOSIP == True )")
            reading = ktl.Expression("($hiccd.OBSERVIP == True) "
                                     "and ($hiccd.WCRATE == True )")
            obsdone = ktl.Expression("($hiccd.OBSERVIP == False)")

            if not exposing.wait(timeout=30):
                raise Exception('Timed out waiting for EXPOSING to start')
            print('  Exposing ...')

            if not reading.wait(timeout=exptime+30):
                raise Exception('Timed out waiting for READING to start')
            print('  Reading out ...')

            if not obsdone.wait(timeout=90):
                raise Exception('Timed out waiting for READING to finish')
            print('Done')

    def get_expo_status(self):
        if self.services is None:
            return None
        EXM0STA = self.services['expo']['EXM0STA'].read()
        return EXM0STA

    def expo_on(self):
        if self.services is None:
            return None
        self.services['expo']['EXM0MOD'].write('On')

    def expo_off(self):
        if self.services is None:
            return None
        self.services['expo']['EXM0MOD'].write('Off')

    def get_lamp(self):
        if self.services is None:
            return None
        lampname = self.services['hires']['LAMPNAME'].read()

    def set_lamp(self, lampname, wait=True):
        if self.services is None:
            return None
        assert lampname in ['none', 'ThAr1', 'ThAr2', 'quartz1', 'quartz2']
        self.services['hires']['LAMPNAME'].write(lampname, wait=wait)
        assert self.get_lamp() == lampname

    def get_lamp_filter(self):
        if self.services is None:
            return None
        lfilname = self.services['hires']['LFILNAME'].read()

    def set_lamp_filter(self, lfilname, wait=True):
        if self.services is None:
            return None
        assert lfilname in ['bg12', 'bg13', 'bg14', 'bg38', 'clear', 'dt',
                            'etalon', 'gg495', 'ng3', 'ug1', 'ug5']
        self.services['hires']['LFILNAME'].write(lfilname, wait=wait)
        assert self.get_lamp_name() == lfilname

# -----------------------------------------------------------------------------
# Afternoon Setup for PRV and Calibrations
# -----------------------------------------------------------------------------
def PRV_afternoon_setup(check_iodine=True):
    '''Configure the instrument for afternoon setup (PRV mode).
    '''
    h = HIRES()
    # Check that lights are off in the HIRES enclosure
    if h.lights_are_on() is True:
        print('WARNING:  Lights in HIRES enclosure are on!')
        print('WARNING:  Enclosure may be occupied, halting script.')
        return False
    # Check dewar level, if below threshold, fill
    if h.get_DWRN2LV() < 30:
        print(f'Dewar level at {h.getDWRN2LV():.1f} %. Initiating dewar fill.')
        h.fill_dewar()
    # Start iodine cell
    h.iodine_start()
    # Open covers
    h.open_covers()
    # --> Set filename root
    # Set binning to 3x1
    h.set_binning('3x1')
    # --> Set full frame
    # Confirm gain=low
    assert h.get_gain() == 'low'
    # Confirm Speed = fast
    assert h.get_speed() == 'fast'
    # m slitname=opened
    h.open_slit()
    # m fil1name=clear
    # m fil2name=clear
    h.set_filters('clear', 'clear')
    # Confirm collimator = red
    assert h.get_collimator() == 'red'
    # m cafraw=0
    h.set_cafraw(0)
    # --> set ECHANG
#     h.services['hires']['ECHANG'].write(0, wait=True)
    # --> set XDANG
#     h.services['hires']['XDANG'].write(0, wait=True)
    # --> tvfilter to BG38
#     h.set_tvfilter('bg38')  # check that tvfocus is set properly
    # Confirm tempiod1 and tempiod2
    if check_iodine is True:
        while h.check_iodine_temps() is not True:
            print('Iodine cell not at temperature.')
            tempiod1, tempiod2 = h.get_iodine_temps()
            print(f'  tempiod1 = {tempiod1:.1f} C')
            print(f'  tempiod2 = {tempiod2:.1f} C')
            print(f'  waiting 5 minutes before checking again (or CTRL-c to exit)')
            sleep(300)
    if h.check_iodine_temps() is True:
        print('Iodine cell at temperature:')
    else:
        print('Iodine cell is not at recommended temperature:')
        tempiod1, tempiod2 = h.get_iodine_temps()
        print(f'  tempiod1 = {tempiod1:.1f} C')
        print(f'  tempiod2 = {tempiod2:.1f} C')

    # Obstype = object
    h.set_obstype('Object')

    # Focus
    # - Exposure meter off
    self.expo_off()
    # - ThAr2 on
    self.set_lamp('ThAr2')
    # - Lamp filter=ng3
    self.set_lamp_filter('ng3')
    # - m deckname=D5
    self.set_decker('D5')
    # - iodine out
    self.iodine_out()
    # - texp = 10 seconds
    self.set_itime(10)
    # - expose
    # - -> run IDL focus routine and iterate as needed


def PRV_calibrations():
    print('Running PRV afternoon calibrations.  Before running this, the '
          'instrument should already be configured for PRV observations.')
    proceed = input('Continue? ')
    if proceed.lower() not in ['y', 'yes', 'ok']:
        print('Exiting calibrations script.')
        return False

    # THORIUM Exposures w/ B5
    # - Exposure meter off
    # - ThAr2 on
    # - lamp filter = ng3
    # - m deckname=B5
    # - iodine out
    # - texp=1 second
    # - two exposures

    # THORIUM Exposure w/ B1
    # - Exposure meter off
    # - ThAr2 on
    # - lamp filter = ng3
    # - m deckname=B1
    # - iodine out
    # - texp=3 second
    # - one exposure
    # - -> check saturation: < 20,000 counts on middle chip?
    # - -> Check I2 line depth. In center of chip, it should be ~30%

    # Iodine Cell Calibrations B5
    # - Make sure cell is fully warmed up before taking these
    # - Exposure meter off
    # - Quartz2 on
    # - Lamp filter=ng3
    # - m deckname=B5
    # - iodine in
    # - texp=2 second
    # - one exposure
    # - -> check saturation: < 20,000 counts on middle chip?
    # - -> Check I2 line depth. In center of chip, it should be ~30%

    # Wide Flat Fields
    # - Exposure meter off
    # - Quartz2 on
    # - Lamp filter=ng3
    # - m deckname=C1
    # - iodine out
    # - texp=1 second
    # - Take 1 exposures
    # - -> Check one test exp for saturation (<20k counts)
    # - Take 49 exposures
    # - m lampname=none
    # - m deckname=C2
    # - Check dewar level, if below threshold, fill
