import unittest
from pymtl3 import *
from src.cl.fetch_stage import FetchStage


class TestFetchStage(unittest.TestCase):
    def setUp(self):
        self.dut = FetchStage()
        self.dut.apply(DefaultPassGroup())
        self.dut.sim_reset()

    def test_recall(self):
        self.dut.icache.load_file("tests/input_files/test_fetch256.csv")
        self.dut.sim_reset()

        self.dut.send.rdy @= 1
        self.assertEqual(self.dut.pc, 0)
        self.assertEqual(self.dut.send.val, 1)
        self.assertEqual(self.dut.send.msg.to_bits(), 0x00010203_04050607)

        self.dut.sim_tick()

        self.assertEqual(self.dut.pc, 8)
        self.assertEqual(self.dut.send.val, 1)
        self.assertEqual(self.dut.send.msg.to_bits(), 0x08090A0B_0C0D0E0F)

        self.dut.sim_tick()

        self.assertEqual(self.dut.pc, 16)
        self.assertEqual(self.dut.send.val, 1)
        self.assertEqual(self.dut.send.msg.to_bits(), 0x10111213_14151617)
