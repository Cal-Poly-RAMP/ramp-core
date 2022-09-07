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
from pymtl3.stdlib.ifcs import RecvIfcRTL, SendIfcRTL

from src.cl.fetch_stage import FetchPacket
from src.cl.register_rename import RegisterRename
from src.cl.branch_allocate import BranchAllocate

from src.common.interfaces import (
    BranchUpdate,
    MicroOp,
    DualMicroOp,
    LogicalRegs,
    PhysicalRegs,
    PRegBusy,
)
from src.common.consts import (
    # fetch
    INSTR_WIDTH,
    # Decoding consts
    OPCODE_SLICE,
    RD_SLICE,
    RS1_SLICE,
    RS2_SLICE,
    FUNCT3_SLICE,
    INSTR_NOP,
    RTYPE_OPCODE,
    ITYPE_OPCODE1,
    ITYPE_OPCODE2,
    ITYPE_OPCODE3,
    STYPE_OPCODE,
    BTYPE_OPCODE,
    UTYPE_OPCODE1,
    UTYPE_OPCODE2,
    JTYPE_OPCODE,
    CSRTYPE_OPCODE,
    # enumerations
    # issue units
    NA_ISSUE_UNIT,
    INT_ISSUE_UNIT,
    MEM_ISSUE_UNIT,
    BRANCH_ISSUE_UNIT,
    # functional units
    NA_FUNCT_UNIT,
    ALU_FUNCT_UNIT,
    MEM_FUNCT_UNIT,
    BRANCH_FUNCT_UNIT,
    # instruction types
    NA_TYPE,
    R_TYPE,
    I_TYPE,
    S_TYPE,
    B_TYPE,
    U_TYPE,
    J_TYPE,
    CSR_TYPE,
    # TODO: move to a file that makes sense, (circular import)
    MEM_Q_SIZE,
    WINDOW_SIZE,
    NUM_BRANCHES,  # maximum depth of nested branches
    NUM_ISA_REGS,
    NUM_PHYS_REGS,
    NUM_ISA_REGS,
    NUM_PHYS_REGS,
)


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

        # for deallocating branch tags
        s.br_update = RecvIfcRTL(BranchUpdate)

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

        # for allocating physical registers and assigning them logical registers
        # TODO: there will be problems if only one instruction in the window is
        # properly allocated registers, and the other is not (full)
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

        # for deallocating branch tags
        s.register_rename.br_update.msg //= s.br_update.msg
        s.register_rename.br_update.en //= s.br_update.en

        # for allocating branch tags and assigning branch masks
        # TODO: there will be problems if only one instruction in the window is
        # properly allocated a branch tag, and the other is not (full)
        s.branch_allocate = BranchAllocate(ntags=8, window_size=2)
        # branch tags out...
        s.d1.br_mask //= s.branch_allocate.br_mask[0]
        s.d1.br_tag //= s.branch_allocate.br_tag[0].msg
        s.d2.br_mask //= s.branch_allocate.br_mask[1]
        s.d2.br_tag //= s.branch_allocate.br_tag[1].msg

        # for deallocating branch tags
        s.branch_allocate.br_update.msg //= s.br_update.msg
        s.branch_allocate.br_update.en //= s.br_update.en

        # from commit stage...
        for x in range(2):
            s.stale_in[x] //= s.register_rename.stale_in[x]
            s.ready_in[x] //= s.register_rename.ready_in[x]

        @update
        def allocate_():
            # allocate memory queue space
            s.mem_q_allocate @= zext(
                s.d1.uop.issue_unit == MEM_ISSUE_UNIT, WINDOW_SIZE
            ) + zext(s.d2.uop.issue_unit == MEM_ISSUE_UNIT, WINDOW_SIZE)

            # allocate branch tags
            s.branch_allocate.br_tag[0].rdy @= s.d1.uop.optype == B_TYPE
            s.branch_allocate.br_tag[1].rdy @= s.d2.uop.optype == B_TYPE

            # connecting branch update signals
            s.br_update.rdy @= s.branch_allocate.br_update.rdy & s.register_rename.br_update.rdy

            # TODO: FOR CL MODEL
            # for i in range(2):
            #     assert ~(s.branch_allocate.br_tag[i].rdy ^ s.branch_allocate.br_tag[i].en)

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
        s.br_tag = InPort(clog2(NUM_BRANCHES))  # branch tag from branch allocate
        s.br_mask = InPort(NUM_BRANCHES)  # branch mask from branch allocate
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
            s.uop.br_tag @= s.br_tag
            s.uop.br_mask @= s.br_mask
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


# Used for deriving data from instructions
@bitstruct
class GenericInstPattern:
    funct7: mk_bits(7)
    rs2: mk_bits(5)
    rs1: mk_bits(5)
    funct3: mk_bits(5)
    rd: mk_bits(5)
    opcode: mk_bits(7)
