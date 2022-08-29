import unittest
from pymtl3 import *
from src.cl.branch_allocate import BranchAllocate

from hypothesis import given, strategies as st

# See Verilog debugging for a more inclusive testcase
NTAGS = 8
class TestBranchAllocate(unittest.TestCase):
    def setUp(s) -> None:
        # runs before every test
        if not hasattr(s, "dut"):
            s.dut = BranchAllocate(ntags=NTAGS)
            s.dut.apply(DefaultPassGroup(textwave=False, linetrace=True))
        s.dut.sim_reset()

    def tearDown(s) -> None:
        # runs after every test
        if s.dut.sim_cycle_count():
            print("final:", s.dut.line_trace())

    # neither instruction are branches, with dealloc
    @given(st.integers(min_value=0, max_value=2**NTAGS-1),
            st.booleans(),
            st.integers(min_value=0, max_value=NTAGS-1))
    def test_two_non_br(s, freelist, dealloc_en, dealloc_msg):
        s.dut.br_freelist @= Bits(NTAGS, freelist)
        s.dut.br_tag[0].rdy @= 0
        s.dut.br_tag[1].rdy @= 0
        s.dut.deallocate_tag.en @= dealloc_en
        s.dut.deallocate_tag.msg @= dealloc_msg

        next_freelist = freelist & ~(1 << dealloc_msg) if dealloc_en else freelist

        s.dut.sim_eval_combinational()
        assert s.dut.br_tag[0].en == 0
        assert s.dut.br_tag[1].en == 0
        assert s.dut.br_mask[0] == next_freelist
        assert s.dut.br_mask[1] == next_freelist

        assert s.dut.full == (next_freelist == Bits(NTAGS, -1))

        s.dut.sim_tick()
        assert s.dut.br_freelist == next_freelist

    # first instruction is a branch
    @given(st.integers(min_value=0, max_value=2**NTAGS-1),
            st.booleans(),
            st.integers(min_value=0, max_value=NTAGS-1))
    def test_first_br(s, freelist, dealloc_en, dealloc_msg):
        s.dut.br_freelist @= Bits(NTAGS, freelist)
        s.dut.br_tag[0].rdy @= 1
        s.dut.br_tag[1].rdy @= 0
        s.dut.deallocate_tag.en @= dealloc_en
        s.dut.deallocate_tag.msg @= dealloc_msg

        next_freelist = Bits(NTAGS)
        next_freelist @= freelist & ~(1 << dealloc_msg) if dealloc_en else freelist

        s.dut.sim_eval_combinational()
        if next_freelist == 2**NTAGS-1:
            assert s.dut.br_tag[0].en == 0
            assert s.dut.br_tag[1].en == 0
            assert s.dut.br_mask[0] == next_freelist
            assert s.dut.br_mask[1] == next_freelist

            assert s.dut.full
            return

        assert s.dut.br_tag[0].en == 1
        assert s.dut.br_tag[1].en == 0

        for b in range(NTAGS):
            if next_freelist[b] == 0:
                assert s.dut.br_tag[0].msg == b
                break

        assert s.dut.br_mask[0] == next_freelist

        next_freelist @= next_freelist | (1 << s.dut.br_tag[0].msg.uint())
        assert s.dut.br_mask[1] == next_freelist

        s.dut.sim_tick()
        assert s.dut.br_freelist == next_freelist

    # second instruction is a branch
    @given(st.integers(min_value=0, max_value=2**NTAGS-1),
            st.booleans(),
            st.integers(min_value=0, max_value=NTAGS-1))
    def test_second_br(s, freelist, dealloc_en, dealloc_msg):
        s.dut.br_freelist @= Bits(NTAGS, freelist)
        s.dut.br_tag[0].rdy @= 0
        s.dut.br_tag[1].rdy @= 1
        s.dut.deallocate_tag.en @= dealloc_en
        s.dut.deallocate_tag.msg @= dealloc_msg

        next_freelist = Bits(NTAGS)
        next_freelist @= freelist & ~(1 << dealloc_msg) if dealloc_en else freelist

        s.dut.sim_eval_combinational()
        if next_freelist == 2**NTAGS-1:
            assert s.dut.br_tag[0].en == 0
            assert s.dut.br_tag[1].en == 0
            assert s.dut.br_mask[0] == next_freelist
            assert s.dut.br_mask[1] == next_freelist

            assert s.dut.full
            return

        assert s.dut.br_tag[0].en == 0
        assert s.dut.br_tag[1].en == 1

        for b in range(NTAGS):
            if next_freelist[b] == 0:
                assert s.dut.br_tag[1].msg == b
                break

        assert s.dut.br_mask[0] == next_freelist
        assert s.dut.br_mask[1] == next_freelist
        next_freelist @= next_freelist | (1 << s.dut.br_tag[1].msg.uint())

        s.dut.sim_tick()
        assert s.dut.br_freelist == next_freelist

    # both instructions are branches
    @given(st.integers(min_value=0, max_value=2**NTAGS-1),
            st.booleans(),
            st.integers(min_value=0, max_value=NTAGS-1))
    def test_both_br(s, freelist, dealloc_en, dealloc_msg):
        s.dut.br_freelist @= Bits(NTAGS, freelist)
        s.dut.br_tag[0].rdy @= 1
        s.dut.br_tag[1].rdy @= 1
        s.dut.deallocate_tag.en @= dealloc_en
        s.dut.deallocate_tag.msg @= dealloc_msg

        next_freelist = Bits(NTAGS)
        next_freelist @= freelist & ~(1 << dealloc_msg) if dealloc_en else freelist

        s.dut.sim_eval_combinational()
        if "{:08b}".format(next_freelist.uint()).count('0') < 2:
            # assert s.dut.br_tag[0].en == 0
            # assert s.dut.br_tag[1].en == 0
            assert s.dut.br_mask[0] == next_freelist
            next_freelist @= next_freelist | (1 << s.dut.br_tag[0].msg.uint())
            assert s.dut.br_mask[1] == next_freelist

            assert s.dut.full
            return

        assert s.dut.br_tag[0].en == 1
        assert s.dut.br_tag[1].en == 1

        c = 0
        for b in range(NTAGS):
            if (next_freelist[b] == 0) & (c < 2):
                print(c)
                assert s.dut.br_tag[c].msg == b
                c = c + 1

        assert s.dut.br_mask[0] == next_freelist
        next_freelist @= next_freelist | (1 << s.dut.br_tag[0].msg.uint())
        assert s.dut.br_mask[1] == next_freelist
        next_freelist @= next_freelist | (1 << s.dut.br_tag[1].msg.uint())

        s.dut.sim_tick()
        assert s.dut.br_freelist == next_freelist

    # TODO: test parameterization