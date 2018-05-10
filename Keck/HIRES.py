import re
from datetime import datetime as dt
from time import sleep

# Wrap ktl import in try/except so that we can maintain test case or simulator
# version of functions.
try:
    import ktl
    from ktl import Exceptions as ktlExceptions
except:
    ktl = None

from Keck.Instruments import AbstractInstrument

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
        self.binnings = ["1x1", "1x2", "2x1", "2x2"]
        self.basename = f"h{dt.utcnow().strftime('%Y%m%d')}_"
        self.serviceNames = ["hires", "hiccd", "expo"]
        self.obstypes = ["object", "dark", "line", "intflat", "bias"]
    
    
    def connect(self):
        if ktl is not None:
            for service in self.serviceNames:
                try:
                    self.services[service] = ktl.Service(service)
                except ktlExceptions.ktlError:
                    print(f"Failed to connect to service {service}")
    
    
    def get_binning(self):
        if ktl is not None:
            keywordresult = self.services['hiccd']['BINNING'].read()
            binningmatch = re.match('\\n\\tXbinning (\d)\\n\\tYbinning (\d)',
                                    keywordresult)
            if binningmatch is not None:
                self.binning = (int(binningmatch.group(1)),
                                int(binningmatch.group(2)))
            else:
                print(f'Could not parse keyword value "{keywordresult}"')
    
    
    def get_DWRN2LV(self):
        if ktl is not None:
            DWRN2LV = float(self.services['hiccd']['DWRN2LV'].read())
        else:
            print('Using simulated results')
            DWRN2LV = 100 - dt.now().minute/60*90 # mock up (100 to 10 each hour)
        return DWRN2LV
    
    
    def get_RESN2LV(self):
        if ktl is not None:
            RESN2LV = float(self.services['hiccd']['RESN2LV'].read())
        else:
            print('Using simulated results')
            RESN2LV = 100 - dt.now().weekday()/6*50 # mock up (100 to 50 each week)
        return RESN2LV
    
    
    def fill_dewar(self):
        print('Initiating camera dewar fill.')
        if ktl is not None:
            pass
    
    
    def take_exposure(self, obstype=None, exptime=None, nexp=1):
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
            exposing = ktl.Expression("($hiccd.OBSERVIP == True) and ($hiccd.EXPOSIP == True )")
            reading = ktl.Expression("($hiccd.OBSERVIP == True) and ($hiccd.WCRATE == True )")
            obsdone = ktl.Expression("($hiccd.OBSERVIP == False)")

            if not exposing.wait(timeout=30):
                raise Exception('Timed out waiting for EXPOSING state to start')
            print('  Exposing ...')

            if not reading.wait(timeout=exptime+30):
                raise Exception('Timed out waiting for READING state to start')
            print('  Reading out ...')

            if not obsdone.wait(timeout=90):
                raise Exception('Timed out waiting for READING state to finish')
            print('Done')


#     def expo_get_power_on(self):
#         return True
#     
#     
#     def expo_toggle_power(self):
#         new_state = not self.expo_get_power_on()
#         print(f'Setting power on exposure meter {{True: "ON", False: "OFF"}[new_state]}')
