from pytest import *
from pytest import Bits, Component, Interface, bitstruct
from pymtl3.stdlib import stream
from cl.fetch_stage import FetchPacket


class Decode(Component):
    def construct(s):
        # Interface (fetch packet)
        s.recv = stream.ifcs.RecvIfcRTL(FetchPacket)
        s.send = stream.ifcs.SendIfcRTL(DualMicroOp)


@bitstruct
class MicroOp(Interface):
    uop_code: Bits(4)  # micro-op type
    inst: Bits(32)  # instruction
    pc: Bits(32)  # program counter

    lrd: Bits(5)  # logical destination register
    lrs1: Bits(5)  # logical source register 1
    lrs2: Bits(5)  # logical source register 2

    prd: Bits(6)  # physical dest register TODO: get bitwidth from phys reg file size
    prs1: Bits(6)  # physical source register 1
    prs2: Bits(6)  # physical source register 2
    stale: Bits(6)  # stale physical register

    prd_busy: Bits(1)  # physical destination register busy
    prs1_busy: Bits(1)  # physical source register 1 busy
    prs2_busy: Bits(1)  # physical source register 2 busy

    imm: Bits(16)  # immediate TODO: encode to be smaller, and use sign extension

    issue_unit: Bits(2)  # issue unit
    fu_unit: Bits(2)  # functional unit
    fu_op: Bits(2)  # functional unit operation

    # TODO: branch prediction


@bitstruct
class DualMicroOp(Interface):
    uop1: MicroOp
    uop2: MicroOp
