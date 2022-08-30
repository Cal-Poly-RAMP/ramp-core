from pymtl3 import Bits

# fetch
ICACHE_ADDR_WIDTH = 8
INSTR_WIDTH = 32

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
ROB_SIZE = 32

MEM_Q_SIZE = 16
MEM_SIZE = 256
WINDOW_SIZE = 2

NUM_BRANCHES = 8  # maximum depth of nested branches

NUM_ISA_REGS = 32

NUM_PHYS_REGS = 64

ISSUE_QUEUE_DEPTH = 16
