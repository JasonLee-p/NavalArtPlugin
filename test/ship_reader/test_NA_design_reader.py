"""
测试NA设计读取器
"""
from ship_reader.NA_design_reader import get_rot_relation as grr
from ship_reader.NA_design_reader import AdjustableHull as AH
import unittest


class TestNaDesignReaderFuncs(unittest.TestCase):
    pos = [0, 0, 0]
    rot = [0, 0, 0]
    scl = [1, 1, 1]
    col = '888888'
    amr = 5
    len = 12
    hei = 3
    fWid = 6
    bWid = 9
    fSpr = 2
    bSpr = 2
    uCur = 0
    dCur = 0
    hScl = 1
    hOff = 0

    H0 = AH(
        None, "0", pos, rot, scl, col, amr,
        len, hei, fWid, bWid, fSpr, bSpr, uCur, dCur,
        hScl, hOff
    )

    def test_get_rot_relation(self):
        orgR = [0., 0., 0.]
        x180R = [180., 0., 0.]
        y180R = [0., 180., 0.]
        z180R = [0., 0., 180.]
        x90R = [90., 0., 0.]
        y90R = [0., 90., 0.]
        xn90R = [270., 0., 0.]
        yn90R = [0., 270., 0.]
        oR = [180., 180., 0.]
        self.assertEqual(grr(orgR, orgR), 'same')
        self.assertEqual(grr(orgR, x180R), 'x')
        self.assertEqual(grr(orgR, y180R), 'y')
        self.assertEqual(grr(orgR, z180R), 'z')
        self.assertEqual(grr(orgR, x90R), 'u')
        self.assertEqual(grr(orgR, xn90R), 'd')
        self.assertEqual(grr(orgR, y90R), 'l')
        self.assertEqual(grr(orgR, yn90R), 'r')
        self.assertEqual(grr(orgR, oR), 'o')

    def test_get_data_in_coordinate(self):
        rots = [[0, 0, 0], [180, 0, 0], [0, 180, 0], [0, 0, 180], [90, 0, 0], [270, 0, 0], [0, 90, 0], [0, 270, 0]]
        for rot in rots:
            self.H0.Rot = rot
            print(f"{rot}: {self.H0.get_data_in_coordinate()}")
