from . import *


class HIRESData(KeckData):
    """Class to represent HIRES data.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
        if self.get('OBSTYPE').upper() == 'BIAS' and self.get('EXPTIME') < 0.1:
            return 'BIAS'
        elif self.get('OBSTYPE').upper() == 'INTFLAT':
            return 'INTFLAT'
        else:
            return None
