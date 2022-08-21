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
        s.dut = MultiInputRdyCircularBuffer(mk_bits(32), size=s.size, num_inports=s.num_inports)
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
        # 0
        assert s.dut.tail == 0
        assert s.dut.head == 0
        assert s.dut.full == 0
        assert s.dut.empty == 1
        assert s.dut.out.en == 0

        # 1 pushing to empty buffer
        s.dut.push_in[0].msg @= 10
        s.dut.push_in[0].en @= 1
        s.dut.push_in[1].msg @= 15
        s.dut.push_in[1].en @= 1
        s.dut.rdy_in[0].en @= 0
        s.dut.rdy_in[1].en @= 0
        s.dut.out.rdy @= 0
        s.dut.sim_tick()

        assert s.dut.tail == 2
        assert s.dut.head == 0
        assert s.dut.full == 0
        assert s.dut.empty == 0
        assert s.dut.out.en == 0

        # 2 checking that nothing will be popped if not ready
        s.dut.push_in[0].en @= 0
        s.dut.push_in[1].en @= 0
        s.dut.rdy_in[0].en @= 0
        s.dut.rdy_in[1].en @= 0
        s.dut.out.rdy @= 1
        s.dut.sim_tick()

        assert s.dut.tail == 2
        assert s.dut.head == 0
        assert s.dut.full == 0
        assert s.dut.empty == 0
        assert s.dut.out.en == 0

        # 2 checking pop if ready
        s.dut.push_in[0].en @= 0
        s.dut.push_in[1].en @= 0
        s.dut.rdy_in[0].msg @= 0
        s.dut.rdy_in[0].en @= 1
        s.dut.rdy_in[1].msg @= 1
        s.dut.rdy_in[1].en @= 1
        s.dut.rdy_in[2].msg @= 2
        s.dut.rdy_in[2].en @= 1
        s.dut.out.rdy @= 1
        s.dut.sim_tick()

        assert s.dut.tail == 2
        assert s.dut.head == 1
        assert s.dut.full == 0
        assert s.dut.empty == 0
        assert s.dut.out.msg == 10
        assert s.dut.out.en == 1

        # 3 checking pop and append simultaneously
        s.dut.push_in[0].en @= 0
        s.dut.push_in[1].msg @= 25
        s.dut.push_in[1].en @= 1
        s.dut.out.rdy @= 1
        s.dut.rdy_in[0].en @= 0
        s.dut.rdy_in[1].en @= 0
        s.dut.rdy_in[2].en @= 0
        s.dut.sim_tick()

        assert s.dut.tail == 3
        assert s.dut.head == 2
        assert s.dut.full == 0
        assert s.dut.empty == 0
        assert s.dut.out.msg == 15
        assert s.dut.out.en == 1

    def test_fill_empty_buffer(s):
        # Loading load store buffer

        for _ in range(10):
            # Filling up buffer
            for i in range(s.num_inports):
                s.dut.push_in[i].en @= 1
                s.dut.rdy_in[0].en @= 0
            s.dut.out.rdy @= 0

            for i in range(0, s.size + s.num_inports, s.num_inports):
                for x in range(s.num_inports):
                    s.dut.push_in[x].msg @= i + x
                s.dut.sim_tick()

            # Checking buffer is full
            assert s.dut.tail == s.dut.head
            assert s.dut.full == 1
            assert s.dut.empty == 0
            tmp = [x.uint() for x in s.dut.buffer]

            # Trying to add more
            for x in range(s.num_inports):
                s.dut.push_in[x].msg @= 10 * x
            s.dut.sim_tick()

            # Checking buffer has not been modified
            assert s.dut.buffer == tmp

            # Emptying buffer
            s.dut.out.rdy @= 1
            for x in range(s.num_inports):
                s.dut.push_in[x].en @= 0
            for i in range(0, s.size):
                s.dut.rdy_in[0].en @= 1
                s.dut.rdy_in[0].msg @= i

                s.dut.sim_tick()
                assert s.dut.out.en == 1
                assert s.dut.out.msg == i

            for i in range(s.num_inports):
                s.dut.push_in[i].en @= 0
                s.dut.rdy_in[0].en @= 0
            s.dut.out.rdy @= 0
            s.dut.sim_tick()
            assert s.dut.tail == s.dut.head
            assert s.dut.full == 0
            assert s.dut.empty == 1
            assert s.dut.out.en == 0