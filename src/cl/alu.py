from pymtl3 import Component, Bits, InPort, OutPort, update, zext, Wire
from src.common.consts import (
    ALU_ADD,
    ALU_SLL,
    ALU_SLT,
    ALU_SLTU,
    ALU_XOR,
    ALU_SRL,
    ALU_OR,
    ALU_AND,
    ALU_SUB,
    ALU_LUI_COPY,
    ALU_SRA,
)


class ALU(Component):
    def construct(s, Type):
        # Defining signals
        s.a = InPort(Type)
        s.b = InPort(Type)
        s.b_sub = Wire(Type)
        s.op = InPort(4)
        s.out = OutPort(Type)

        ONES = Bits(Type.nbits)
        ONES @= -1

        # combinatorial logic
        @update
        def updt():
            # s.b[4:0] (for 32 bit) s.b[7:0] (for 64 bit)
            s.b_sub @= s.b & (Type.nbits - 1)

            # ADD
            if s.op == ALU_ADD:
                s.out @= s.a + s.b
            # SUB
            elif s.op == ALU_SUB:
                s.out @= s.a - s.b
            # OR
            elif s.op == ALU_OR:
                s.out @= s.a | s.b
            # AND
            elif s.op == ALU_AND:
                s.out @= s.a & s.b
            # XOR
            elif s.op == ALU_XOR:
                s.out @= s.a ^ s.b
            # Shift Right Logical
            elif s.op == ALU_SRL:
                s.out @= s.a >> s.b_sub
            # Shift Left Logical
            elif s.op == ALU_SLL:
                # s.a << s.b[4:0] (for 32 bit)
                s.out @= s.a << s.b_sub
            # Shift Right Arithmetic
            elif s.op == ALU_SRA:
                # s.a >>> s.b[4:0] (for 32 bit)
                if s.a[Type.nbits - 1]:
                    s.out @= (s.a >> s.b_sub) | ~(ONES >> s.b_sub)
                else:
                    s.out @= s.a >> s.b_sub
            # Set Less Than TODO: `and` may not work
            elif s.op == ALU_SLT:
                if s.a[Type.nbits - 1] ^ s.b[Type.nbits - 1]:
                    s.out @= zext(s.a[Type.nbits - 1], Type.nbits)
                elif s.a < s.b:
                    s.out @= 1
                else:
                    s.out @= 0
            # Set Less Than Unsigned
            elif s.op == ALU_SLTU:
                s.out @= 1 if (s.a < s.b) else 0  # TODO: Better way to do this?
            # Load Upper Immediate Copy
            elif s.op == ALU_LUI_COPY:
                s.out @= s.b
            else:
                s.out @= 0

    def line_trace(s):
        return f"op: {s.op} a: {s.a} b: {s.b} out: {s.out}"
