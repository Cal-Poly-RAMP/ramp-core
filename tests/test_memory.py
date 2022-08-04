import unittest
import os
from tempfile import TemporaryDirectory
from hypothesis import given, strategies as st
from pymtl3 import *
from src.cl.memory import Memory

addr_width = 8
data_width = 8
word_width = 32
dpw = word_width // data_width


class TestMemory(unittest.TestCase):
    def setUp(self):
        self.mem = Memory(
            addr_width=addr_width, data_width=data_width, word_width=word_width
        )
        self.mem.apply(DefaultPassGroup())
        self.mem.sim_reset()

    @given(
        st.integers(min_value=0, max_value=2**addr_width - dpw - 1),
        st.integers(min_value=0, max_value=2**word_width - 1),
    )
    def test_rw_word(self, addr, data):
        addr = Bits(self.mem.addr_width, addr)
        data = Bits(self.mem.word_width, data)

        self.mem.write_word(addr, data)
        self.assertEqual(self.mem.read_word(addr), data)

    def test_load_save_file(self):
        # TODO: change JSON or use CSV module
        with TemporaryDirectory() as tmpdir:
            tmpfilepath = os.path.join(tmpdir, "test.csv")

            self.mem.load_file("tests/input_files/test_mem256.csv")
            self.mem.save_file(tmpfilepath)

            with open("tests/input_files/test_mem256.csv", "r") as f1:
                d1 = f1.read().replace("\n", "").replace(" ", "").split(",")[:-1]
            with open(tmpfilepath) as f2:
                d2 = f2.read().replace("\n", "").replace(" ", "").split(",")[:-1]

        self.assertEqual(d1, d2)
        self.assertEqual(len(d1), len(self.mem.mem))

    def test_load_exception(self):
        with self.assertRaises(ValueError):
            self.mem.load_file("tests/input_files/test_mem16.csv")
