from . import *


class MOSFIREData(KeckData):
    """Class to represent MOSFIRE data.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instrument = 'MOSFIRE'

    def verify(self):
        """Verifies that the data which was read in matches an expected pattern
        """
        if len(self.headers) != 5:
            raise IncorrectNumberOfExtensions("header", "5", self)
        if len(self.pixeldata) not in [1, 2, 3]:
            raise IncorrectNumberOfExtensions("pixel", "1, 2, or 3", self)
        if len(self.tabledata) != 4:
            raise IncorrectNumberOfExtensions("table", "4", self)

    def type(self):
        obsmode = self.get('OBSMODE')

        # Is the arc lamp on?
        arcpower = (self.get('PWSTATA7', mode=bool) is True\
                    or self.get('PWSTATA8', mode=bool) is True)

        # Is telescope in flatlamp position
        domeaz = self.get('DOMEPOSN', mode=float)
        az = self.get('AZ', mode=float)
        flatlampPos = (abs(self.get('EL', mode=float) - 45) < 0.1\
                          and abs(abs(domeaz - az) - 90) < 1)

        # Is the dust cover open
        if (self.get('MDCMECH') == 'Dust Cover' and self.get('MDCSTAT') == 'OK'):
            dustCover = self.get('MDCNAME').lower()

        # Dome lamp keyword values
        flatOn = self.get('FLATSPEC', mode=bool) is True\
                     or self.get('FLIMAGIN') == 'on'\
                     or self.get('FLSPECTR') == 'on'

        # Determine Image Type
        # Dark frame
        if 'dark' in obsmode.lower() and not arcpower:
            return 'DARK'
        else:
            # arclamp
            if dustCover == 'closed':
                if 'spectroscopy' in obsmode and arcpower:
                    return 'ARC'
            elif dustCover == 'open':
                # This is an object unless a flatlamp is on
                if flatOn is True:
                    return 'FLAT'
                elif flatlampPos is True:
                    return 'FLATOFF'
                else:
                    return 'OBJECT'

        # Still undefined? Use image statistics
        # Is the telescope in dome flat position?
        if flatlampPos is True:
            if np.mean(self.pixeldata[0].data) > 500:
                return 'FLAT'
            else:
                return 'FLATOFF'

        # if we got here, we couldn't match any of the above cases, so *shrug*
        return None

    def filename(self):
        KOAID = self.get('KOAID', None)
        if KOAID is None:
            return f"{self.get('DATAFILE')}.fits"
        return KOAID

    def exptime(self):
        """Return the exposure time in seconds.
        """
        exptime = float(self.get('TRUITIME')) * int(self.get('COADDONE'))
        return exptime
