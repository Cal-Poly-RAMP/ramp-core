import unittest
from pymtl3 import DefaultPassGroup
from src.cl.fetch_stage import FetchStage, FetchPacket
from src.fl.util import get_mem

from src.common.consts import ICACHE_SIZE


class TestFetchStage(unittest.TestCase):
    def test_recall(self):
        # TODO: write tests, working for system tests
        return
        self.dut = FetchStage(data=get_mem("tests/input_files/test_load_store.bin", ICACHE_SIZE))
        self.dut.apply(
            DefaultPassGroup(
                textwave=True, vcdwave="vcd/test_front_end"
            )
        )
        self.dut.sim_reset()

        self.dut.br_update.en @= 0

        self.assertEqual(
            self.dut.fetch_packet,
            FetchPacket(inst1=0x00800093, inst2=0x02a00113, pc=0, valid=1),
        )

        self.dut.sim_tick()
        self.assertEqual(
            self.dut.fetch_packet,
            FetchPacket(inst1=0xfe20ae23, inst2=0xffc0a183, pc=8, valid=1),
        )

        self.dut.sim_tick()
        self.assertEqual(
            self.dut.fetch_packet,
            FetchPacket(inst1=0x00310233, inst2=0, pc=16, valid=1),
        )

    # TODO: create a test using hypothesis for random testing of different sizes
