import unittest
from pymtl3 import *
from src.cl.branch_fu import BranchFU
from src.cl.decode import (
    BFU_BEQ,
    BFU_BNE,
    BFU_BLT,
    BFU_BGE,
    BFU_BLTU,
    BFU_BGEU,
    BRANCH_FUNCT_UNIT,
    MicroOp,
)
from hypothesis import given, strategies as st

# defining hypothesis strategies
@st.composite
def branch_input(draw, op):
    uop = MicroOp(0)
    uop.funct_unit @= BRANCH_FUNCT_UNIT
    uop.funct_op @= op
    uop.pc @= draw(st.integers(min_value=0, max_value=2**32-1))
    uop.imm @= draw(st.integers(min_value=0, max_value=2**32-1))
    uop.branch_taken @= draw(st.booleans())

    rs1 = draw(st.integers(min_value=-(2 ** (32 - 1)), max_value=2 ** (32 - 1)))
    rs2 = draw(st.integers(min_value=-(2 ** (32 - 1)), max_value=2 ** (32 - 1)))

    return uop, rs1, rs2

# See Verilog debugging for a more inclusive testcase
class TestALU(unittest.TestCase):
    def setUp(s) -> None:
        # runs before every test
        if not hasattr(s, "dut"):
            s.dut = BranchFU()
            s.dut.apply(DefaultPassGroup(textwave=False, linetrace=True))
        s.dut.sim_reset()

    def tearDown(s) -> None:
        # runs after every test
        if s.dut.sim_cycle_count():
            print("final:", s.dut.line_trace())

    # equals
    @given(branch_input(BFU_BEQ))
    def test_beq(s, branch_input):
        uop, rs1, rs2 = branch_input
        s.dut.rs1_din @= rs1
        s.dut.rs2_din @= rs2
        s.dut.uop @= uop

        s.dut.sim_tick()
        # correctly predicted
        if rs1 == rs2 and uop.branch_taken:
            s.assertEqual(s.dut.mispredict.en, 0)
        # incorrectly predicted
        elif rs1 == rs2 and not uop.branch_taken:
            s.assertEqual(s.dut.mispredict.en, 1)
            s.assertEqual(s.dut.mispredict.msg, uop.pc + uop.imm)
        # incorrectly predicted
        elif rs1 != rs2 and uop.branch_taken:
            s.assertEqual(s.dut.mispredict.en, 1)
            s.assertEqual(s.dut.mispredict.msg, uop.pc + 8)
        # correctly predicted
        elif rs1 != rs2 and not uop.branch_taken:
            s.assertEqual(s.dut.mispredict.en, 0)
        else:
            assert False, "should not reach here"

    # not equals
    @given(branch_input(BFU_BNE))
    def test_bne(s, branch_input):
        uop, rs1, rs2 = branch_input
        s.dut.rs1_din @= rs1
        s.dut.rs2_din @= rs2
        s.dut.uop @= uop

        s.dut.sim_tick()
        # correctly predicted
        if rs1 != rs2 and uop.branch_taken:
            s.assertEqual(s.dut.mispredict.en, 0)
        # incorrectly predicted
        elif rs1 != rs2 and not uop.branch_taken:
            s.assertEqual(s.dut.mispredict.en, 1)
            s.assertEqual(s.dut.mispredict.msg, uop.pc + uop.imm)
        # incorrectly predicted
        elif rs1 == rs2 and uop.branch_taken:
            s.assertEqual(s.dut.mispredict.en, 1)
            s.assertEqual(s.dut.mispredict.msg, uop.pc + 8)
        # correctly predicted
        elif rs1 == rs2 and not uop.branch_taken:
            s.assertEqual(s.dut.mispredict.en, 0)
        else:
            assert False, "should not reach here"

    # less than
    @given(branch_input(BFU_BLT))
    def test_blt(s, branch_input):
        uop, rs1, rs2 = branch_input
        s.dut.rs1_din @= rs1
        s.dut.rs2_din @= rs2
        s.dut.uop @= uop

        s.dut.sim_tick()
        # correctly predicted
        if rs1 < rs2 and uop.branch_taken:
            s.assertEqual(s.dut.mispredict.en, 0)
        # incorrectly predicted
        elif rs1 < rs2 and not uop.branch_taken:
            s.assertEqual(s.dut.mispredict.en, 1)
            s.assertEqual(s.dut.mispredict.msg, uop.pc + uop.imm)
        # incorrectly predicted
        elif rs1 >= rs2 and uop.branch_taken:
            s.assertEqual(s.dut.mispredict.en, 1)
            s.assertEqual(s.dut.mispredict.msg, uop.pc + 8)
        # correctly predicted
        elif rs1 >= rs2 and not uop.branch_taken:
            s.assertEqual(s.dut.mispredict.en, 0)
        else:
            assert False, "should not reach here"

    # greater than or equal
    @given(branch_input(BFU_BGE))
    def test_bge(s, branch_input):
        uop, rs1, rs2 = branch_input
        s.dut.rs1_din @= rs1
        s.dut.rs2_din @= rs2
        s.dut.uop @= uop

        s.dut.sim_tick()
        # correctly predicted
        if rs1 >= rs2 and uop.branch_taken:
            s.assertEqual(s.dut.mispredict.en, 0)
        # incorrectly predicted
        elif rs1 >= rs2 and not uop.branch_taken:
            s.assertEqual(s.dut.mispredict.en, 1)
            s.assertEqual(s.dut.mispredict.msg, uop.pc + uop.imm)
        # incorrectly predicted
        elif rs1 < rs2 and uop.branch_taken:
            s.assertEqual(s.dut.mispredict.en, 1)
            s.assertEqual(s.dut.mispredict.msg, uop.pc + 8)
        # correctly predicted
        elif rs1 < rs2 and not uop.branch_taken:
            s.assertEqual(s.dut.mispredict.en, 0)
        else:
            assert False, "should not reach here"

    # # less than unsigned TODO: working in code but need to finish t4ests
    # @given(branch_input(BFU_BLTU))
    # def test_bltu(s, branch_input):
    #     uop, rs1, rs2 = branch_input
    #     s.dut.rs1_din @= rs1
    #     s.dut.rs2_din @= rs2
    #     s.dut.uop @= uop

    #     s.dut.sim_tick()
    #     # correctly predicted
    #     if rs1 < rs2 and uop.branch_taken:
    #         s.assertEqual(s.dut.mispredict.en, 0)
    #     # incorrectly predicted
    #     elif rs1 < rs2 and not uop.branch_taken:
    #         s.assertEqual(s.dut.mispredict.en, 1)
    #         s.assertEqual(s.dut.mispredict.msg, uop.pc + uop.imm)
    #     # incorrectly predicted
    #     elif rs1 >= rs2 and uop.branch_taken:
    #         s.assertEqual(s.dut.mispredict.en, 1)
    #         s.assertEqual(s.dut.mispredict.msg, uop.pc + 8)
    #     # correctly predicted
    #     elif rs1 >= rs2 and not uop.branch_taken:
    #         s.assertEqual(s.dut.mispredict.en, 0)
    #     else:
    #         assert False, "should not reach here"

    # # greater than or equal unsigned
    # @given(branch_input(BFU_BGEU))
    # def test_bgeu(s, branch_input):
    #     uop, rs1, rs2 = branch_input
    #     s.dut.rs1_din @= rs1
    #     s.dut.rs2_din @= rs2
    #     s.dut.uop @= uop

    #     s.dut.sim_tick()
    #     # correctly predicted
    #     if rs1 >= rs2 and uop.branch_taken:
    #         s.assertEqual(s.dut.mispredict.en, 0)
    #     # incorrectly predicted
    #     elif rs1 >= rs2 and not uop.branch_taken:
    #         s.assertEqual(s.dut.mispredict.en, 1)
    #         s.assertEqual(s.dut.mispredict.msg, uop.pc + uop.imm)
    #     # incorrectly predicted
    #     elif rs1 < rs2 and uop.branch_taken:
    #         s.assertEqual(s.dut.mispredict.en, 1)
    #         s.assertEqual(s.dut.mispredict.msg, uop.pc + 8)
    #     # correctly predicted
    #     elif rs1 < rs2 and not uop.branch_taken:
    #         s.assertEqual(s.dut.mispredict.en, 0)
    #     else:
    #         assert False, "should not reach here"



if __name__ == "__main__":
    unittest.main()
    suite = unittest.TestLoader().loadTestsFromTestCase(TestALU)
    unittest.TextTestRunner(verbosity=2).run(suite)
