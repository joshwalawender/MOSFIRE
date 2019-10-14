from . import *


class HIRESData(KeckData):
    """Class to represent HIRES data.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instrument = 'HIRES'

    def verify(self):
        """Verifies that the data which was read in matches an expected pattern
        """
        if len(self.headers) != 4:
            raise IncorrectNumberOfExtensions("header", "4", self)
        if len(self.pixeldata) not in [1, 2, 3]:
            raise IncorrectNumberOfExtensions("pixel", "1, 2, or 3", self)
        if len(self.tabledata) != 0:
            raise IncorrectNumberOfExtensions("table", "0", self)

    def type(self):
        if self.get('OBSTYPE').upper() == 'BIAS' and float(self.get('DARKTIME')) < 2:
            return 'BIAS'
        elif self.get('OBSTYPE').upper() == 'DARK':
            return 'DARK'
        elif self.get('OBSTYPE').upper() == 'INTFLAT':
            return 'INTFLAT'
        else:
            return None

    def filename(self):
        return f"{self.get('OUTFILE')}{int(self.get('FRAMENO')):04d}.fits"

    def exptime(self):
        """Return the exposure time in seconds.
        """
        if self.type() in ['BIAS', 'DARK']:
            return float(self.get('DARKTIME'))
        else:
            return float(self.get('EXPTIME'))
