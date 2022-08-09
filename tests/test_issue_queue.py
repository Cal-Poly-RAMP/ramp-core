import unittest
from pymtl3 import *
from src.cl.issue_queue import IssueQueue

class TestIssueQueue(unittest.TestCase):
    def setUp(s) -> None:
        # runs before every test
        if not hasattr(s, "dut"):
            s.dut = IssueQueue()
            s.dut.apply(DefaultPassGroup(textwave=True, linetrace=True))
        s.dut.sim_reset()

    def tearDown(s) -> None:
        # runs after every test
        if s.dut.sim_cycle_count():
            print("final:", s.dut.line_trace())
            s.dut.print_textwave()

    def test(s):
        pass