import re
from datetime import datetime as dt
from time import sleep

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
        self.connect()

    def get_collimator(self):
        '''Determine which collimator is in the beam.  Returns a string of
        'red' or 'blue' indicating which is in beam.  Returns None if it can
        not interpret the result.
        '''
        collred = self.services['hires']['COLLRED'].read()
        collblue = self.services['hires']['COLLBLUE'].read()
        if collred == 'red' and collblue == 'not blue':
            collimator = 'red'
        elif collred == 'not red' and collblue == 'blue':
            collimator = 'blue'
        else:
            collimator = None
        return collimator

    def lights_are_on(self):
        '''Returns True if lights are on in the enclosure.
        '''
        return self.services['hires']['lights'].read() == 'on'

    def get_iodine_temps(self):
        '''Returns the iodine cell temperatures (tempiod1, tempiod2) in units
        of degrees C.
        '''
        if self.services is None:
            return None
        tempiod1 = float(self.services['hires']['tempiod1'].read())
        tempiod2 = float(self.services['hires']['tempiod2'].read())
        return [tempiod1, tempiod2]

    def check_iodine_temps(self, target1=65, target2=50, range=0.1):
        '''Checks the iodine cell temperatures agains the given targets and
        range.  Default values are those used by the CPS team.
        '''
        if self.services is None:
            return None
        tempiod1, tempiod2 = self.get_iodine_temps()
        if abs(tempiod1 - target1) < range and abs(tempiod2 - target2) < range:
            return True
        else:
            return False

    def get_binning(self):
        '''Populates the binning property and return the value.  Both are a
        tuple of (binX, binY).
        '''
        if self.services is None:
            return None
        keywordresult = self.services['hiccd']['BINNING'].read()
        binningmatch = re.match('\\n\\tXbinning (\d)\\n\\tYbinning (\d)',
                                keywordresult)
        if binningmatch is not None:
            self.binning = (int(binningmatch.group(1)),
                            int(binningmatch.group(2)))
            return self.binning
        else:
            print(f'Could not parse keyword value "{keywordresult}"')
            return None

    def _set_binning(self, binX, binY):
        '''Private method called by the set_binning method of the
        AbstractInstrument class.  That method should be used by users, this
        method captures the exact keyword commands to change binning for each
        specific instrument.
        '''
        if self.services is None:
            return None
        self.services['hiccd']['BINNING'].write((binX, binY))
        assert (binX, binY) == self.get_binning()

    def get_DWRN2LV(self):
        '''Returns a float of the current camera dewar level, supposedly in
        percentage, but as this is poorly calibrated, it maxes out at nearly
        120% as of mid 2018.
        '''
        if self.services is None:
            return None
        DWRN2LV = float(self.services['hiccd']['DWRN2LV'].read())
        return DWRN2LV

    def get_RESN2LV(self):
        '''Returns a float of the current reserve dewar level.  Each camera
        dewar fill takes roughly 10% of the reserve dewar.
        '''
        if self.services is None:
            return None
        RESN2LV = float(self.services['hiccd']['RESN2LV'].read())
        return RESN2LV

    def fill_dewar(self, wait=True):
        '''Fill camera dewar using procedure in /local/home/hireseng/bin/filln2
        '''
        if self.services is None:
            return None
        if self.services['hiccd']['WCRATE'].read() is not False:
            print('The CCD is currently reading out. Try again when complete.')
            return None
        print('Initiating camera dewar fill.')
        self.services['hiccd']['utbn2fil'].write('on')
        while self.services['hiccd']['utbn2fil'].read() != 'off':
            sleep(15)
        print('HIRES Dewar Fill is Complete.')
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
        collimator = self.get_collimator()

        if collimator == 'red':
            self.services['hires']['rcocover'].write('open', wait=False)
        elif collimator == 'blue':
            self.services['hires']['bcocover'].write('open', wait=False)
        else:
            print('Collimator is unknown.  Collimator cover not opened.')
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
                print('Collimator is unknown.  Collimator cover not opened.')
            self.services['hires']['echcover'].write('open', wait=True)
            self.services['hires']['co1cover'].write('open', wait=True)
            self.services['hires']['xdcover'].write('open', wait=True)
            self.services['hires']['co2cover'].write('open', wait=True)
            self.services['hires']['camcover'].write('open', wait=True)
            self.services['hires']['darkslid'].write('open', wait=True)

    def close_covers(self, wait=True):
        '''Closes all internal covers.
        '''
        collimator = self.get_collimator()

        if collimator == 'red':
            self.services['hires']['rcocover'].write('closed', wait=False)
        elif collimator == 'blue':
            self.services['hires']['bcocover'].write('closed', wait=False)
        else:
            print('Collimator is unknown.  Collimator cover not opened.')
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
                print('Collimator is unknown.  Collimator cover not opened.')
            self.services['hires']['echcover'].write('closed', wait=True)
            self.services['hires']['co1cover'].write('closed', wait=True)
            self.services['hires']['xdcover'].write('closed', wait=True)
            self.services['hires']['co2cover'].write('closed', wait=True)
            self.services['hires']['camcover'].write('closed', wait=True)
            self.services['hires']['darkslid'].write('closed', wait=True)

    def iodine_start(self):
        '''Starts the iodine cell heater.  Cell takes ~45 minutes to warm up.
        
        Use same process as in /local/home/hires/bin/iod_start

        modify -s hires moniodt=1
        modify -s hires setiodt=50.
        modify -s hires iodheat=on
        '''
        if self.services is None:
            return None
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
        self.services['hires']['moniodt'].write(0)
        self.services['hires']['iodheat'].write('off')

    def open_slit(self, wait=True):
        '''Open the slit jaws.
        '''
        self.services['hires']['slitname'].write('opened', wait=wait)

    def set_filters(self, fil1name, fil2name, wait=True):
        '''Set the filter wheels.
        '''
        self.services['hires']['fil1name'].write(fil1name, wait=wait)
        self.services['hires']['fil2name'].write(fil2name, wait=wait)

    def set_cafraw(self, cafraw, wait=True):
        self.services['hires']['cafraw'].write(cafraw, wait=wait)

    def set_cofraw(self, cofraw, wait=True):
        self.services['hires']['cofraw'].write(cafraw, wait=wait)

    def set_tvfilter(self, tvf1name, wait=True):
        self.services['hires']['TVF1NAME'].write(tvf1name, wait=wait)

    def set_obstype(self, obstype):
        if obstype in self.obstypes:
            self.services['hiccd']['obstype'].write(obstype)
        else:
            print(f'OBSTYPE {obstype} not recognized.')
            print(f'Allowed obstypes:')
            for otype in self.obstypes:
                print(f'  {otype}')

    def take_exposure(self, obstype=None, exptime=None, nexp=1):
        '''Takes one or more exposures of the given exposure time and type.
        Modeled after goi script.
        '''
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

#     def expo_get_power_on(self):
#         return True
#
#     def expo_toggle_power(self):
#         new_state = not self.expo_get_power_on()
#         print(f'Exposure meter {{True: "ON", False: "OFF"}[new_state]}')


# -----------------------------------------------------------------------------
# Afternoon Setup for PRV and Calibrations
# -----------------------------------------------------------------------------
def PRV_afternoon_setup():
    '''Configure the instrument for afternoon setup (PRV mode).
    '''
    h = HIRES()
    h.connect()
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
    # Set filename root
    # Set binning to 3x1
    h.set_binning('3x1')
    # Set full frame
    # Confirm gain=low
    # Confirm Speed = fast
    # m slitname=opened
    h.open_slit()
    # m fil1name=clear
    # m fil2name=clear
    h.set_filters('clear', 'clear')
    # Confirm collimator = red
    assert h.get_collimator() == 'red'
    # m cafraw=0
    h.set_cafraw(0)
    # set ECHANG
#     h.services['hires']['ECHANG'].write(0, wait=True)
    # set XDANG
#     h.services['hires']['XDANG'].write(0, wait=True)
    # tvfilter to BG38
    h.set_tvfilter('bg38')
    # Confirm tempiod1 and tempiod2
    while h.check_iodine_temps() is not True:
        print('Iodine cell not at temperature.')
        tempiod1, tempiod2 = h.get_iodine_temps()
        print(f'  tempiod1 = {tempiod1:.1f} C')
        print(f'  tempiod2 = {tempiod2:.1f} C')
        print(f'  waiting 5 minutes before checking again (or CTRL-c to exit)')
        sleep(300)
    if h.check_iodine_temps() is True:
        print('Iodine cell at temperature:')
        tempiod1, tempiod2 = h.get_iodine_temps()
        print(f'  tempiod1 = {tempiod1:.1f} C')
        print(f'  tempiod2 = {tempiod2:.1f} C')

    # Obstype = object
    h.set_obstype('Object')

    # Focus
    # - Exposure meter off
    # - ThAr2 on
    # - Lamp filter=ng3
    # - m deckname=D5
    # - iodine out
    # - texp = 10 seconds
    # - expose
    # - -> run IDL focus routine and iterate as needed

    # Calibrations

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
