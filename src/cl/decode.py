from sre_constants import BRANCH
from pymtl3 import (
    Bits,
    Bits1,
    Bits4,
    Bits12,
    Component,
    InPort,
    OutPort,
    Wire,
    bitstruct,
    concat,
    mk_bits,
    sext,
    zext,
    update,
    clog2,
)
from src.cl.fetch_stage import FetchPacket, INSTR_WIDTH
from src.cl.register_rename import (
    ISA_REG_BITWIDTH,
    NUM_ISA_REGS,
    NUM_PHYS_REGS,
    PHYS_REG_BITWIDTH,
    LogicalRegs,
    PhysicalRegs,
    PRegBusy,
    RegisterRename,
)
from src.cl.branch_allocate import BranchAllocate

# Decoding consts
OPCODE_SLICE = slice(0, 7)
RD_SLICE = slice(7, 12)
RS1_SLICE = slice(15, 20)
RS2_SLICE = slice(20, 25)
FUNCT3_SLICE = slice(12, 15)
FUNCT7_SLICE = slice(25, 32)

INSTR_NOP = 0x00000013  # a nop instruction

RTYPE_OPCODE = 0b0110011
ITYPE_OPCODE1 = 0b0010011
ITYPE_OPCODE2 = 0b0000011
ITYPE_OPCODE3 = 0b1100111
STYPE_OPCODE = 0b0100011
BTYPE_OPCODE = 0b1100011
UTYPE_OPCODE1 = 0b0110111
UTYPE_OPCODE2 = 0b0010111
JTYPE_OPCODE = 0b1101111
CSRTYPE_OPCODE = 0b1110011

# enumerations
# issue units
NA_ISSUE_UNIT = 0b00
INT_ISSUE_UNIT = 0b01
MEM_ISSUE_UNIT = 0b10
BRANCH_ISSUE_UNIT = 0b11

# functional units
NA_FUNCT_UNIT = 0b00
ALU_FUNCT_UNIT = 0b01
MEM_FUNCT_UNIT = 0b10
BRANCH_FUNCT_UNIT = 0b11

# instruction types
NA_TYPE = 0b00
R_TYPE = 0b001
I_TYPE = 0b010
S_TYPE = 0b011
B_TYPE = 0b100
U_TYPE = 0b101
J_TYPE = 0b110
CSR_TYPE = 0b111

# ALU functions [funct7[5], funct3]
ALU_ADD = Bits(4, 0b0000)
ALU_SUB = Bits(4, 0b1000)
ALU_OR = Bits(4, 0b0110)
ALU_AND = Bits(4, 0b0111)
ALU_XOR = Bits(4, 0b0100)
ALU_SRL = Bits(4, 0b0101)
ALU_SLL = Bits(4, 0b0001)
ALU_SRA = Bits(4, 0b1101)
ALU_SLT = Bits(4, 0b0010)
ALU_SLTU = Bits(4, 0b0011)
ALU_LUI_COPY = Bits(4, 0b1001)

# memory functions [opcode[5], funct3]
MEM_LB = Bits(4, 0b0000)
MEM_LH = Bits(4, 0b0001)
MEM_LW = Bits(4, 0b0010)
MEM_LBU = Bits(4, 0b0100)
MEM_LHU = Bits(4, 0b0101)
MEM_LOAD = Bits(4, 0b0000)
MEM_SB = Bits(4, 0b1000)
MEM_SH = Bits(4, 0b1001)
MEM_SW = Bits(4, 0b1010)
MEM_STORE = Bits(4, 0b1000)
MEM_FLAG = Bits(4, 0b1000)  # flag for determining load or store

# branch functions [0, funct3]
BFU_BEQ = Bits(4, 0b0000)
BFU_BNE = Bits(4, 0b0001)
BFU_BLT = Bits(4, 0b0100)
BFU_BGE = Bits(4, 0b0101)
BFU_BLTU = Bits(4, 0b0110)
BFU_BGEU = Bits(4, 0b0111)

# TODO: move to a file that makes sense, (circular import)
ROB_ADDR_WIDTH = 5
ROB_SIZE = 2**ROB_ADDR_WIDTH

MEM_Q_SIZE = 16
MEM_SIZE = 256
WINDOW_SIZE = 2

NUM_BRANCHES = 8 # maximum depth of nested branches


class Decode(Component):
    # For decoding fetch packet into two micro-ops
    def construct(s):
        # Interface (fetch packet in, dual uops out)
        s.fetch_packet = InPort(FetchPacket)
        s.inst1 = Wire(32)
        s.inst2 = Wire(32)
        s.inst1 //= s.fetch_packet.inst1
        s.inst2 //= s.fetch_packet.inst2

        s.dual_uop = OutPort(DualMicroOp)
        s.busy_table = OutPort(NUM_PHYS_REGS)
        # for allocating space in load/store queue
        s.mem_q_allocate = OutPort(WINDOW_SIZE)

        # register to be freed (from commit stage)
        s.stale_in = [InPort(clog2(NUM_PHYS_REGS)) for _ in range(2)]
        # register to be marked as 'not busy' (from commit stage)
        s.ready_in = [InPort(clog2(NUM_PHYS_REGS)) for _ in range(2)]

        s.d1 = SingleInstDecode()
        # instruction in
        s.d1.inst //= s.inst1
        s.d1.pc //= s.fetch_packet.pc
        s.d1.branch_taken //= s.fetch_packet.branch_taken
        s.d1.idx = 0
        # uop out...
        s.d1.uop //= s.dual_uop.uop1
        s.d1.valid //= s.fetch_packet.valid

        s.d2 = SingleInstDecode()
        # instruction in
        s.d2.inst //= s.inst2
        s.d2.pc //= s.fetch_packet.pc
        s.d2.branch_taken //= s.fetch_packet.branch_taken
        s.d2.idx = 1
        # uop out...
        s.d2.uop //= s.dual_uop.uop2
        s.d2.valid //= s.fetch_packet.valid

        s.register_rename = RegisterRename()
        # logical registers in...
        s.register_rename.inst1_lregs.lrd //= s.d1.uop.lrd
        s.register_rename.inst1_lregs.lrs1 //= s.d1.uop.lrs1
        s.register_rename.inst1_lregs.lrs2 //= s.d1.uop.lrs2
        s.register_rename.inst2_lregs.lrd //= s.d2.uop.lrd
        s.register_rename.inst2_lregs.lrs1 //= s.d2.uop.lrs1
        s.register_rename.inst2_lregs.lrs2 //= s.d2.uop.lrs2
        # physical registers out...
        s.register_rename.inst1_pregs.prd //= s.d1.pregs.prd
        s.register_rename.inst1_pregs.prs1 //= s.d1.pregs.prs1
        s.register_rename.inst1_pregs.prs2 //= s.d1.pregs.prs2
        s.register_rename.inst1_pregs.stale //= s.d1.pregs.stale
        s.register_rename.inst2_pregs.prd //= s.d2.pregs.prd
        s.register_rename.inst2_pregs.prs1 //= s.d2.pregs.prs1
        s.register_rename.inst2_pregs.prs2 //= s.d2.pregs.prs2
        s.register_rename.inst2_pregs.stale //= s.d2.pregs.stale

        # pregs busy status out...
        s.register_rename.inst1_pregs_busy //= s.d1.pregs_busy
        s.register_rename.inst2_pregs_busy //= s.d2.pregs_busy

        # busy table
        s.busy_table //= s.register_rename.busy_table

        # from commit stage...
        for x in range(2):
            s.stale_in[x] //= s.register_rename.stale_in[x]
            s.ready_in[x] //= s.register_rename.ready_in[x]

        @update
        def allocate_():
            s.mem_q_allocate @= zext(
                s.d1.uop.issue_unit == MEM_ISSUE_UNIT, WINDOW_SIZE
            ) + zext(s.d2.uop.issue_unit == MEM_ISSUE_UNIT, WINDOW_SIZE)

    def line_trace(s):
        return (
            f"\tfetch packet:\t{s.fetch_packet}"
            + f"\n\tuop1:\t{s.dual_uop.uop1} \n\tuop2:\t{s.dual_uop.uop2}"
        )


class SingleInstDecode(Component):
    # For decoding a single instruction into one micro-op, with info from register renaming
    def construct(s):
        s.inst = InPort(INSTR_WIDTH)  # instruction from fetch packet
        s.pc = InPort(32)  # pc from fetch packet
        s.branch_taken = InPort(1)  # branch taken from fetch packet
        s.idx = InPort()  # index of instruction in fetch packet (0, 1)
        s.mem_q_idx = InPort(clog2(MEM_Q_SIZE))  # tail of load/store queue
        s.pregs = InPort(PhysicalRegs)  # physical registers from register rename
        s.pregs_busy = InPort(PRegBusy)  # busy table from register rename
        s.valid = InPort()  # valid bit from fetch packet
        s.uop = OutPort(MicroOp)

        @update
        def decode_comb():
            # defaults
            s.uop.inst @= s.inst
            s.uop.pc @= (s.pc + 4) if s.idx else (s.pc)
            s.uop.branch_taken @= s.branch_taken
            s.uop.valid @= (s.inst != INSTR_NOP) & ~(s.inst == 0)

            # TODO: Currently, register renaming is dependent on not-used
            # logical registers being zeroed out. If we want to get rid of the
            # zeroing out logic, register renaming must be changed.
            s.uop.lrd @= s.inst[RD_SLICE]
            s.uop.lrs1 @= s.inst[RS1_SLICE]
            s.uop.lrs2 @= s.inst[RS2_SLICE]

            s.uop.prd @= s.pregs.prd
            s.uop.prs1 @= s.pregs.prs1
            s.uop.prs2 @= s.pregs.prs2
            s.uop.stale @= s.pregs.stale

            s.uop.imm @= 0
            s.uop.funct_op @= 0
            s.uop.rob_idx @= 0
            s.uop.mem_q_idx @= 0

            # For determining type
            opcode = s.inst[OPCODE_SLICE]
            # arithmetic and logical instructions
            if opcode == RTYPE_OPCODE:
                s.uop.optype @= R_TYPE
                s.uop.issue_unit @= INT_ISSUE_UNIT
                s.uop.funct_unit @= ALU_FUNCT_UNIT
                s.uop.funct_op @= concat(s.inst[30], s.inst[FUNCT3_SLICE])

            # immediate arithmetic and logical
            elif opcode == ITYPE_OPCODE1:
                s.uop.optype @= I_TYPE
                s.uop.issue_unit @= INT_ISSUE_UNIT
                s.uop.funct_unit @= ALU_FUNCT_UNIT
                s.uop.funct_op @= zext(s.inst[FUNCT3_SLICE], 4)
                # srli, srai
                if s.inst[FUNCT3_SLICE] == 0b101:
                    s.uop.funct_op @= concat(s.inst[30], s.inst[FUNCT3_SLICE])
                s.uop.imm @= sext(s.inst[20:32], 32)

                s.uop.lrs2 @= 0
            # loads
            elif opcode == ITYPE_OPCODE2:
                s.uop.optype @= I_TYPE
                s.uop.issue_unit @= MEM_ISSUE_UNIT
                s.uop.funct_unit @= MEM_FUNCT_UNIT
                s.uop.funct_op @= concat(opcode[5], s.inst[FUNCT3_SLICE])
                s.uop.imm @= sext(s.inst[20:32], 32)

                s.uop.lrs2 @= 0
            # jalr
            elif opcode == ITYPE_OPCODE3:
                s.uop.optype @= I_TYPE
                s.uop.issue_unit @= BRANCH_ISSUE_UNIT
                s.uop.funct_unit @= BRANCH_FUNCT_UNIT
                s.uop.funct_op @= 0
                s.uop.imm @= sext(s.inst[20:32], 32)

                s.uop.lrs2 @= 0
            # stores
            elif opcode == STYPE_OPCODE:
                s.uop.optype @= S_TYPE
                s.uop.issue_unit @= MEM_ISSUE_UNIT
                s.uop.funct_unit @= MEM_FUNCT_UNIT
                s.uop.funct_op @= concat(opcode[5], s.inst[FUNCT3_SLICE])
                s.uop.imm @= sext(concat(s.inst[25:32], s.inst[7:12]), 32)

                s.uop.lrd @= 0
            # branches
            elif opcode == BTYPE_OPCODE:
                s.uop.optype @= B_TYPE
                s.uop.issue_unit @= BRANCH_ISSUE_UNIT
                s.uop.funct_unit @= BRANCH_FUNCT_UNIT
                s.uop.funct_op @= zext(s.inst[FUNCT3_SLICE], 4)
                s.uop.imm @= sext(
                    concat(
                        s.inst[31], s.inst[7], s.inst[25:31], s.inst[8:12], Bits1(0)
                    ),
                    32,
                )

                s.uop.lrd @= 0
            # lui (1), auipc (2)
            elif (opcode == UTYPE_OPCODE1) | (opcode == UTYPE_OPCODE2):
                s.uop.optype @= U_TYPE
                s.uop.issue_unit @= INT_ISSUE_UNIT
                s.uop.funct_unit @= ALU_FUNCT_UNIT
                s.uop.funct_op @= Bits4(0b1001)  # alu lui-copy TODO: auipc
                s.uop.imm @= concat(s.inst[12:32], Bits12(0))

                s.uop.lrs1 @= 0
                s.uop.lrs2 @= 0
            # jal
            elif opcode == JTYPE_OPCODE:
                s.uop.optype @= J_TYPE
                s.uop.issue_unit @= BRANCH_ISSUE_UNIT
                s.uop.funct_unit @= BRANCH_FUNCT_UNIT
                s.uop.imm @= sext(
                    concat(
                        s.inst[31],
                        s.inst[12:20],
                        s.inst[20],
                        s.inst[25:31],
                        s.inst[21:25],
                        Bits1(0),
                    ),
                    32,
                )

                s.uop.lrs1 @= 0
                s.uop.lrs2 @= 0
            # system instructions
            elif opcode == CSRTYPE_OPCODE:
                s.uop.optype @= CSR_TYPE
                s.uop.issue_unit @= NA_ISSUE_UNIT
                s.uop.funct_unit @= NA_FUNCT_UNIT
                s.uop.funct_op @= 0
                s.uop.imm @= 0

                s.uop.lrs2 @= 0
            # otherwise noop
            else:
                s.uop.optype @= NA_TYPE
                s.uop.issue_unit @= NA_ISSUE_UNIT
                s.uop.funct_unit @= NA_FUNCT_UNIT
                s.uop.funct_op @= 0
                s.uop.imm @= 0
                s.uop.lrs2 @= 0
                s.uop.lrs1 @= 0
                s.uop.lrd @= 0
                s.uop.stale @= 0


@bitstruct
class MicroOp:
    optype: mk_bits(3)  # micro-op type
    inst: mk_bits(INSTR_WIDTH)  # instruction
    pc: mk_bits(32)  # program counter TODO: just forward to ROB?
    valid: mk_bits(1)  # whether this is a valid uop (not noop)

    lrd: mk_bits(ISA_REG_BITWIDTH)  # logical destination register
    lrs1: mk_bits(ISA_REG_BITWIDTH)  # logical source register 1
    lrs2: mk_bits(ISA_REG_BITWIDTH)  # logical source register 2

    prd: mk_bits(PHYS_REG_BITWIDTH)  # physical dest register
    prs1: mk_bits(PHYS_REG_BITWIDTH)  # physical source register 1
    prs2: mk_bits(PHYS_REG_BITWIDTH)  # physical source register 2
    stale: mk_bits(PHYS_REG_BITWIDTH)  # stale physical register

    # immediate TODO: encode to be smaller, and use sign extension TODO: 64 bit?
    imm: mk_bits(32)

    issue_unit: mk_bits(2)  # issue unit
    funct_unit: mk_bits(2)  # functional unit
    funct_op: mk_bits(4)  # functional unit operation

    branch_taken: mk_bits(1)  # whether branch was taken
    br_mask: mk_bits(NUM_BRANCHES) # bitmask corresponding to pred branches
    br_tag: mk_bits(clog2(NUM_BRANCHES)) # branch tag (for branch instructions)

    rob_idx: mk_bits(ROB_ADDR_WIDTH)  # index of instruction in ROB
    mem_q_idx: mk_bits(clog2(MEM_Q_SIZE))  # index of instruction in memory queue

    def __str__(s):
        return (
            f"optype: {s.optype} inst: {s.inst} pc: {s.pc}"
            f" valid: {s.valid} imm: {s.imm}"
            f" i_unit: {s.issue_unit} f_unit: {s.funct_unit} f_op: {s.funct_op}"
            f" lr : {s.lrd.uint():02d}:{s.lrs1.uint():02d}:{s.lrs2.uint():02d}"
            f" pr : {s.prd.uint():02d}:{s.prs1.uint():02d}:{s.prs2.uint():02d}"
            f" stale: x{s.stale.uint():02d}"
            f" rob_idx: {s.rob_idx}"
        )

    def __bool__(self):
        return bool(self.valid)


NO_OP = Bits(MicroOp.nbits, 0)  # no-op uop, invalid bit is automatically set to zero


@bitstruct
class DualMicroOp:
    uop1: MicroOp
    uop2: MicroOp

    def __str__(s):
        return f"{s.uop1}\n\t{s.uop2}"

    def __bool__(self):
        return bool(self.uop1) or bool(self.uop2)


# Used for deriving data from instructions
@bitstruct
class GenericInstPattern:
    funct7: mk_bits(7)
    rs2: mk_bits(5)
    rs1: mk_bits(5)
    funct3: mk_bits(5)
    rd: mk_bits(5)
    opcode: mk_bits(7)
