"""
测试NA设计读取器
"""
from ship_reader.NA_design_reader import get_rot_relation as grr
import unittest


class TestNaDesignReaderFuncs(unittest.TestCase):
    def test_get_rot_relation(self):
        orgR = [0, 0, 0]
        x180R = [180, 0, 0]
        y180R = [0, 180, 0]
        z180R = [0, 0, 180]
        x90R = [90, 0, 0]
        y90R = [0, 90, 0]
        # z90R = [0, 0, 90]
        xn90R = [270, 0, 0]
        yn90R = [0, 270, 0]
        # zn90R = [0, 0, 270]
        oR = [180, 180, 0]
        self.assertEqual(grr(orgR, orgR), None)
        self.assertEqual(grr(orgR, x180R), 'x')
        self.assertEqual(grr(orgR, y180R), 'y')
        self.assertEqual(grr(orgR, z180R), 'z')
        self.assertEqual(grr(orgR, x90R), 'u')
        self.assertEqual(grr(orgR, xn90R), 'd')
        self.assertEqual(grr(orgR, y90R), 'l')
        self.assertEqual(grr(orgR, yn90R), 'r')
        self.assertEqual(grr(orgR, oR), 'o')
