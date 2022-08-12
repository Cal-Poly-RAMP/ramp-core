import unittest
from pymtl3 import DefaultPassGroup
from src.cl.fetch_stage import FetchStage, FetchPacket


class TestFetchStage(unittest.TestCase):
    def setUp(self):
        self.dut = FetchStage()
        self.dut.apply(
            DefaultPassGroup(
                textwave=True, linetrace=True, vcdwave="vcd/test_front_end"
            )
        )
        self.dut.sim_reset()

    def test_recall(self):
        self.dut.icache.load_file("tests/input_files/test_fetch256.csv")

        self.dut.sim_eval_combinational()
        print(self.dut.icache.memory)
        print(self.dut.icache_data)
        print(self.dut.icache_data[0:32], self.dut.icache_data[32 : 2 * 32])
        self.assertEqual(
            self.dut.fetch_packet,
            FetchPacket(inst1=0x00010203, inst2=0x04050607, pc=0, valid=1),
        )

        self.dut.sim_tick()
        self.assertEqual(
            self.dut.fetch_packet,
            FetchPacket(inst1=0x08090A0B, inst2=0x0C0D0E0F, pc=8, valid=1),
        )

        self.dut.sim_tick()
        self.assertEqual(
            self.dut.fetch_packet,
            FetchPacket(inst1=0x10111213, inst2=0x14151617, pc=16, valid=1),
        )

    # TODO: create a test using hypothesis for random testing of different sizes
