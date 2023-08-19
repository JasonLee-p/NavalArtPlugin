import xml.etree.ElementTree as ET


class ReadNA:
    def __init__(self, filename):
        self.filename = filename
        self.NA = self.readNA()

    def readNA(self):
        with open(self.filename, 'r') as f:
            NA = f.read()
        return NA
