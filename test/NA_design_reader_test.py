from ship_reader.NA_design_reader import ReadNA as Reader
import unittest


class TestReadNA(unittest.TestCase):
    path = "KMS Hindenburg.na"
    ShipReader = Reader(path)

    def test(self):
        print(TestReadNA.ShipReader.ColorPartsMap)
