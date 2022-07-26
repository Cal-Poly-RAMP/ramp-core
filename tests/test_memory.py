import unittest
from os import remove
from hypothesis import given, strategies as st
from pymtl3 import *
from src.fl.memory import Memory

addr_width = 8
data_width = 8
word_width = 32
dpw = word_width // data_width


class TestMemory1(unittest.TestCase):
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
        self.mem.load_file("tests/input_files/test_mem256.csv")
        self.mem.save_file("test.csv")

        try:
            with open("tests/input_files/test_mem256.csv", "r") as f1:
                with open("test.csv") as f2:
                    d1 = f1.read().replace("\n", "").replace(" ", "").split(",")[:-1]
                    d2 = f2.read().replace("\n", "").replace(" ", "").split(",")[:-1]

                    self.assertEqual(d1, d2)
                    self.assertEqual(len(d1), len(self.mem.mem))
        finally:
            remove("test.csv")

    def test_load_exception(self):
        with self.assertRaises(ValueError):
            self.mem.load_file("tests/input_files/test_mem16.csv")
