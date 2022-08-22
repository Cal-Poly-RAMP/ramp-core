import unittest
from pymtl3 import *

from src.cl.memory_unit import (
    MemoryUnit,
    MultiInputRdyCircularBuffer,
)
from src.cl.decode import MicroOp, Decode


class TestMultiInputRdyCircularBuffer(unittest.TestCase):
    def setUp(s) -> None:
        # runs before every test
        s.size = 8
        s.num_inports = 2
        s.dut = MultiInputRdyCircularBuffer(
            mk_bits(32), size=s.size, num_inports=s.num_inports
        )
        s.dut.apply(
            DefaultPassGroup(
                textwave=True, linetrace=True, vcdwave="vcd/test_memory_unit"
            )
        )
        s.dut.sim_reset()

    def tearDown(s) -> None:
        # runs after every test
        if s.dut.sim_cycle_count():
            print("final:", s.dut.line_trace())
            s.dut.print_textwave()

    def test_multi_input_rdy_circular_buffer(s):
        # 0 - defaults
        def default():
            s.dut.allocate_in.en @= 0
            s.dut.allocate_in.msg @= 0
            s.dut.out.rdy @= 1
            for i in range(s.num_inports):
                s.dut.update_in[i].en @= 0
                s.dut.update_in[i].msg @= 0
                s.dut.update_idx_in[i].en @= 0
                s.dut.update_idx_in[i].msg @= 0

        default()
        assert s.dut.tail == 0
        assert s.dut.head == 0
        assert s.dut.full == 0
        assert s.dut.empty == 1
        assert s.dut.out.en == 0
        assert s.dut.n_elements == 0

        # 1 - allocating two items to empty buffer
        s.dut.allocate_in.en @= 1
        s.dut.allocate_in.msg @= 2
        s.dut.sim_tick()

        assert s.dut.tail == 2
        assert s.dut.head == 0
        assert s.dut.full == 0
        assert s.dut.empty == 0
        assert s.dut.out.en == 0
        assert s.dut.n_elements == 2

        # 2 - updating second item, nothing should be popped
        default()
        s.dut.update_idx_in[0].en @= 1
        s.dut.update_idx_in[0].msg @= 1
        s.dut.update_in[0].en @= 1
        s.dut.update_in[0].msg @= 0xDEADBEEF
        s.dut.sim_tick()

        assert s.dut.tail == 2
        assert s.dut.head == 0
        assert s.dut.full == 0
        assert s.dut.empty == 0
        assert s.dut.out.en == 0
        assert s.dut.n_elements == 2

        # 3 - updating first item, first item should be popped (simultaneous)
        default()
        s.dut.update_idx_in[0].en @= 1
        s.dut.update_idx_in[0].msg @= 0
        s.dut.update_in[0].en @= 1
        s.dut.update_in[0].msg @= 0xABCDEF01
        s.dut.sim_tick()

        assert s.dut.tail == 2
        assert s.dut.head == 1
        assert s.dut.full == 0
        assert s.dut.empty == 0
        assert s.dut.out.en == 1
        assert s.dut.out.msg == 0xABCDEF01
        assert s.dut.n_elements == 1

        # 4 - output disabled, nothing should be popped
        default()
        s.dut.out.rdy @= 0
        s.dut.sim_tick()

        assert s.dut.tail == 2
        assert s.dut.head == 1
        assert s.dut.full == 0
        assert s.dut.empty == 0
        assert s.dut.out.en == 0
        assert s.dut.n_elements == 1

        # 5 - output enabled, second item should be popped
        default()
        s.dut.out.rdy @= 1
        s.dut.sim_tick()

        assert s.dut.tail == 2
        assert s.dut.head == 2
        assert s.dut.full == 0
        assert s.dut.empty == 1
        assert s.dut.out.en == 1
        assert s.dut.out.msg == 0xDEADBEEF
        assert s.dut.n_elements == 0

    def test_fill_empty_buffer(s):
        # Loading load store buffer
        s.dut.allocate_in.en @= 1
        s.dut.allocate_in.msg @= s.size
        s.dut.sim_tick()

        assert s.dut.tail == 0
        assert s.dut.head == 0
        assert s.dut.full == 1
        assert s.dut.empty == 0
        assert s.dut.n_elements == s.size

        # systemically emptying buffer
        s.dut.out.rdy @= 1
        for i in range(s.size):
            s.dut.update_idx_in[0].en @= 1
            s.dut.update_idx_in[0].msg @= i
            s.dut.update_in[0].en @= 1
            s.dut.update_in[0].msg @= i
            s.dut.sim_tick()

        assert s.dut.tail == 0
        assert s.dut.head == 0
        assert s.dut.full == 0
        assert s.dut.empty == 1
        assert s.dut.n_elements == 0
