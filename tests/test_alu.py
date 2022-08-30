import unittest
from pymtl3 import *
from src.cl.alu import ALU
from src.common.consts import (
    ALU_ADD,
    ALU_SLL,
    ALU_SLT,
    ALU_SLTU,
    ALU_XOR,
    ALU_SRL,
    ALU_OR,
    ALU_AND,
    ALU_SUB,
    ALU_LUI_COPY,
    ALU_SRA,
)
from hypothesis import given, strategies as st

BITWIDTH = 32

# See Verilog debugging for a more inclusive testcase
class TestALU(unittest.TestCase):
    def setUp(s) -> None:
        # runs before every test
        if not hasattr(s, "dut"):
            s.dut = ALU(mk_bits(BITWIDTH))
            s.dut.apply(DefaultPassGroup(textwave=False, linetrace=True))
        s.dut.sim_reset()

    def tearDown(s) -> None:
        # runs after every test
        if s.dut.sim_cycle_count():
            print("final:", s.dut.line_trace())

    @given(
        st.integers(min_value=0, max_value=2**BITWIDTH - 1),
        st.integers(min_value=0, max_value=2**BITWIDTH - 1),
    )
    def test_add(s, a, b):
        s.dut.a @= a
        s.dut.b @= b
        s.dut.op @= ALU_ADD
        s.dut.sim_tick()
        # overflow checked
        s.assertEqual(s.dut.out, (a + b) % 2**BITWIDTH)

    @given(
        st.integers(min_value=0, max_value=2**BITWIDTH - 1),
        st.integers(min_value=0, max_value=2**BITWIDTH - 1),
    )
    def test_sub(s, a, b):
        s.dut.a @= a
        s.dut.b @= b
        s.dut.op @= ALU_SUB
        s.dut.sim_tick()
        # overflow checked
        s.assertEqual(s.dut.out, Bits(32, (a - b) % 2**BITWIDTH))

    @given(
        st.integers(min_value=0, max_value=2**BITWIDTH - 1),
        st.integers(min_value=0, max_value=2**BITWIDTH - 1),
    )
    def test_or(s, a, b):
        s.dut.a @= a
        s.dut.b @= b
        s.dut.op @= ALU_OR
        s.dut.sim_tick()
        s.assertEqual(s.dut.out, (a | b))

    @given(
        st.integers(min_value=0, max_value=2**BITWIDTH - 1),
        st.integers(min_value=0, max_value=2**BITWIDTH - 1),
    )
    def test_and(s, a, b):
        s.dut.a @= a
        s.dut.b @= b
        s.dut.op @= ALU_AND
        s.dut.sim_tick()
        s.assertEqual(s.dut.out, (a & b))

    @given(
        st.integers(min_value=0, max_value=2**BITWIDTH - 1),
        st.integers(min_value=0, max_value=2**BITWIDTH - 1),
    )
    def test_xor(s, a, b):
        s.dut.a @= a
        s.dut.b @= b
        s.dut.op @= ALU_XOR
        s.dut.sim_tick()
        s.assertEqual(s.dut.out, (a ^ b))

    @given(
        st.integers(min_value=0, max_value=2**BITWIDTH - 1),
        st.integers(min_value=0, max_value=2**BITWIDTH - 1),
    )
    def test_srl(s, a, b):
        s.dut.a @= a
        s.dut.b @= b
        s.dut.op @= ALU_SRL
        # s.b[4:0] for 32 bit, s.b[7:0] for 64 bit
        b_sub = Bits(BITWIDTH, b) & (BITWIDTH - 1)
        s.dut.sim_tick()
        # shifting by bottom four bits
        s.assertEqual(s.dut.out, Bits(BITWIDTH, a) >> b_sub)

    @given(
        st.integers(min_value=0, max_value=2**BITWIDTH - 1),
        st.integers(min_value=0, max_value=2**BITWIDTH - 1),
    )
    def test_sll(s, a, b):
        s.dut.a @= a
        s.dut.b @= b
        s.dut.op @= ALU_SLL
        # s.b[4:0] for 32 bit, s.b[7:0] for 64 bit
        b_sub = Bits(BITWIDTH, b) & (BITWIDTH - 1)
        s.dut.sim_tick()
        s.assertEqual(s.dut.out, (Bits(BITWIDTH, a) << b_sub))

    @given(
        st.integers(min_value=0, max_value=2**BITWIDTH - 1),
        st.integers(min_value=0, max_value=2**BITWIDTH - 1),
    )
    def test_sra(s, a, b):
        s.dut.a @= a
        s.dut.b @= b
        s.dut.op @= ALU_SRA
        # s.b[4:0] for 32 bit, s.b[7:0] for 64 bit
        b_sub = Bits(BITWIDTH, b) & (BITWIDTH - 1)
        s.dut.sim_tick()

        if s.dut.a[BITWIDTH - 1]:
            s.assertEqual(
                s.dut.out, (Bits(BITWIDTH, a) >> b_sub) | ~(Bits(BITWIDTH, -1) >> b_sub)
            )
            # s.out @= (s.a >> s.b) | ~(ONES >> s.b_sub)
        else:
            s.assertEqual(s.dut.out, (Bits(BITWIDTH, a) >> b_sub))

    @given(
        st.integers(min_value=-(2 ** (BITWIDTH - 1)), max_value=2 ** (BITWIDTH - 1)),
        st.integers(min_value=-(2 ** (BITWIDTH - 1)), max_value=2 ** (BITWIDTH - 1)),
    )
    def test_slt(s, a, b):
        s.dut.a @= a
        s.dut.b @= b
        s.dut.op @= ALU_SLT
        s.dut.sim_tick()
        s.assertEqual(s.dut.out, 1 if a < b else 0)

    @given(
        st.integers(min_value=0, max_value=2**BITWIDTH - 1),
        st.integers(min_value=0, max_value=2**BITWIDTH - 1),
    )
    def test_sltu(s, a, b):
        s.dut.a @= a
        s.dut.b @= b
        s.dut.op @= ALU_SLTU
        s.dut.sim_tick()
        s.assertEqual(s.dut.out, 1 if a < b else 0)

    @given(
        st.integers(min_value=0, max_value=2**BITWIDTH - 1),
        st.integers(min_value=0, max_value=2**BITWIDTH - 1),
    )
    def test_lui_copy(s, a, b):
        s.dut.a @= a
        s.dut.b @= b
        s.dut.op @= ALU_LUI_COPY
        s.dut.sim_tick()
        s.assertEqual(s.dut.out, Bits(BITWIDTH, b))


if __name__ == "__main__":
    unittest.main()
    suite = unittest.TestLoader().loadTestsFromTestCase(TestALU)
    unittest.TextTestRunner(verbosity=2).run(suite)
