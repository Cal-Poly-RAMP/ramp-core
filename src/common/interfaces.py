from pymtl3 import clog2, mk_bits, Bits, bitstruct
from src.common.consts import (
    INSTR_WIDTH,
    NUM_ISA_REGS,
    NUM_PHYS_REGS,
    NUM_BRANCHES,
    ROB_SIZE,
    MEM_Q_SIZE,
)


@bitstruct
class FetchPacket:
    pc: mk_bits(32)
    branch_taken: mk_bits(1)
    inst1: mk_bits(32)
    inst2: mk_bits(32)
    valid: mk_bits(1)


@bitstruct
class MicroOp:
    optype: mk_bits(3)  # micro-op type
    inst: mk_bits(INSTR_WIDTH)  # instruction
    pc: mk_bits(32)  # program counter TODO: just forward to ROB?
    valid: mk_bits(1)  # whether this is a valid uop (not noop)

    lrd: mk_bits(clog2(NUM_ISA_REGS))   # logical destination register
    lrs1: mk_bits(clog2(NUM_ISA_REGS))  # logical source register 1
    lrs2: mk_bits(clog2(NUM_ISA_REGS))  # logical source register 2

    prd: mk_bits(clog2(NUM_PHYS_REGS))  # physical dest register
    prs1: mk_bits(clog2(NUM_PHYS_REGS)) # physical source register 1
    prs2: mk_bits(clog2(NUM_PHYS_REGS)) # physical source register 2
    stale: mk_bits(clog2(NUM_PHYS_REGS))# stale physical register

    # immediate TODO: encode to be smaller, and use sign extension TODO: 64 bit?
    imm: mk_bits(32)

    issue_unit: mk_bits(2)  # issue unit
    funct_unit: mk_bits(2)  # functional unit
    funct_op: mk_bits(4)  # functional unit operation

    branch_taken: mk_bits(1)  # whether branch was taken
    br_mask: mk_bits(NUM_BRANCHES)  # bitmask corresponding to pred branches
    br_tag: mk_bits(clog2(NUM_BRANCHES))  # branch tag (for branch instructions)

    rob_idx: mk_bits(clog2(ROB_SIZE))  # index of instruction in ROB
    mem_q_idx: mk_bits(clog2(MEM_Q_SIZE))  # index of instruction in memory queue

    def __str__(s):
        return (
            f"optype: {s.optype} inst: {s.inst} pc: {s.pc}"
            f" valid: {s.valid} imm: {s.imm}"
            f" i_unit: {s.issue_unit} f_unit: {s.funct_unit} f_op: {s.funct_op}"
            f" br_taken: {s.branch_taken} br_mask: {s.br_mask} br_tag: {s.br_tag}"
            f" lr : {s.lrd.uint():02d}:{s.lrs1.uint():02d}:{s.lrs2.uint():02d}"
            f" pr : {s.prd.uint():02d}:{s.prs1.uint():02d}:{s.prs2.uint():02d}"
            f" stale: x{s.stale.uint():02d}"
            f" rob_idx: {s.rob_idx}"
            f" mem_q_idx: {s.mem_q_idx}"
        )

    def __bool__(self):
        return bool(self.valid)


NO_OP = Bits(MicroOp.nbits, 0)  # no-op uop, invalid bit is automatically set to zero


@bitstruct
class DualMicroOp:
    uop1: MicroOp
    uop2: MicroOp

    # def __str__(s):
    #     return f"{s.uop1}\n\t{s.uop2}"

    def __bool__(self):
        return bool(self.uop1) or bool(self.uop2)


# used for updating modules with an evaluated branch tag
@bitstruct
class BranchUpdate:
    target: mk_bits(32)
    mispredict: mk_bits(1)
    tag: mk_bits(clog2(8))


@bitstruct
class LogicalRegs:
    lrd: mk_bits(clog2(NUM_ISA_REGS))  # logical destination register
    lrs1: mk_bits(clog2(NUM_ISA_REGS))  # logical source register 1
    lrs2: mk_bits(clog2(NUM_ISA_REGS))  # logical source register 2


@bitstruct
class PhysicalRegs:
    prd: mk_bits(
        clog2(NUM_PHYS_REGS)
    )  # physical dest register TODO: get bitwidth from phys reg file size
    prs1: mk_bits(clog2(NUM_PHYS_REGS))  # physical source register 1
    prs2: mk_bits(clog2(NUM_PHYS_REGS))  # physical source register 2
    stale: mk_bits(clog2(NUM_PHYS_REGS))  # stale physical register


@bitstruct
class PRegBusy:
    prs1: mk_bits(1)
    prs2: mk_bits(1)

@bitstruct
class IOEntry:
    addr: mk_bits(32)
    data: mk_bits(32)