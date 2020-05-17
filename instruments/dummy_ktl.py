# ktl dummy package

class cache(object):

    def __init__(self, service='service', keyword='keyword'):
        print(f"WARNING: Not connected to KTL.  Using dummy interface.")
        self.service = service
        self.keyword = keyword

    def read(self):
        print(f'Reading value: {self.service}.{self.keyword}')
        return None

    def write(self, input):
        print(f'Writing value: {input}')
