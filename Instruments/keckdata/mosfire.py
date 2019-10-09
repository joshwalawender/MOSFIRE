from . import *


class MOSFIREData(KeckData):
    """Class to represent MOSFIRE data.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
        return self.get('OBJECT').upper()

