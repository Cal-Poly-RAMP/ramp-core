//-------------------------------------------------------------------------
// ALU.v
//-------------------------------------------------------------------------
// This file is generated by PyMTL SystemVerilog translation pass.

// PyMTL Component ALU Definition
// Full name: ALU__Type_Bits32
// At /Users/curtisbucher/Desktop/ramp-core/src/cl/alu.py

module ALU
(
  input  logic [31:0] a ,
  input  logic [31:0] b ,
  input  logic [0:0] clk ,
  input  logic [3:0] op ,
  output logic [31:0] out ,
  input  logic [0:0] reset 
);
  localparam logic [3:0] __const__ALU_ADD  = 4'd0;
  localparam logic [3:0] __const__ALU_SUB  = 4'd8;
  localparam logic [3:0] __const__ALU_OR  = 4'd6;
  localparam logic [3:0] __const__ALU_AND  = 4'd7;
  localparam logic [3:0] __const__ALU_XOR  = 4'd4;
  localparam logic [3:0] __const__ALU_SRL  = 4'd5;
  localparam logic [3:0] __const__ALU_SLL  = 4'd1;
  localparam logic [3:0] __const__ALU_SRA  = 4'd13;
  localparam logic [31:0] __const__ONES_at_updt  = 32'd4294967295;
  localparam logic [3:0] __const__ALU_SLT  = 4'd2;
  localparam logic [3:0] __const__ALU_SLTU  = 4'd3;
  localparam logic [3:0] __const__ALU_LUI_COPY  = 4'd9;
  logic [31:0] b_sub;

  // PyMTL Update Block Source
  // At /Users/curtisbucher/Desktop/ramp-core/src/cl/alu.py:30
  // @update
  // def updt():
  //     # s.b[4:0] (for 32 bit) s.b[7:0] (for 64 bit)
  //     s.b_sub @= ( s.b & (Type.nbits - 1) )
  // 
  //     # ADD
  //     if s.op == ALU_ADD:
  //         s.out @= s.a + s.b
  //     # SUB
  //     elif s.op == ALU_SUB:
  //         s.out @= s.a - s.b
  //     # OR
  //     elif s.op == ALU_OR:
  //         s.out @= s.a | s.b
  //     # AND
  //     elif s.op == ALU_AND:
  //         s.out @= s.a & s.b
  //     # XOR
  //     elif s.op == ALU_XOR:
  //         s.out @= s.a ^ s.b
  //     # Shift Right Logical
  //     elif s.op == ALU_SRL:
  //         s.out @= s.a >> s.b_sub
  //     # Shift Left Logical
  //     elif s.op == ALU_SLL:
  //         # s.a << s.b[4:0] (for 32 bit)
  //         s.out @= s.a << s.b_sub
  //     # Shift Right Arithmetic
  //     elif s.op == ALU_SRA:
  //         # s.a >>> s.b[4:0] (for 32 bit)
  //         if s.a[Type.nbits - 1]:
  //             s.out @= (s.a >> s.b_sub) | ~(ONES >> s.b_sub)
  //         else:
  //             s.out @= s.a >> s.b_sub
  //     # Set Less Than TODO: `and` may not work
  //     elif s.op == ALU_SLT:
  //         if s.a[Type.nbits - 1] ^ s.b[Type.nbits - 1]:
  //             s.out @= zext(s.a[Type.nbits - 1], Type.nbits)
  //         elif s.a < s.b:
  //             s.out @= 1
  //         else:
  //             s.out @= 0
  //     # Set Less Than Unsigned
  //     elif s.op == ALU_SLTU:
  //         s.out @= 1 if (s.a < s.b) else 0  # TODO: Better way to do this?
  //     # Load Upper Immediate Copy
  //     elif s.op == ALU_LUI_COPY:
  //         s.out @= s.a << 12
  //     else:
  //         s.out @= 0
  
  always_comb begin : updt
    b_sub = b & ( 32'd32 - 32'd1 );
    if ( op == 4'( __const__ALU_ADD ) ) begin
      out = a + b;
    end
    else if ( op == 4'( __const__ALU_SUB ) ) begin
      out = a - b;
    end
    else if ( op == 4'( __const__ALU_OR ) ) begin
      out = a | b;
    end
    else if ( op == 4'( __const__ALU_AND ) ) begin
      out = a & b;
    end
    else if ( op == 4'( __const__ALU_XOR ) ) begin
      out = a ^ b;
    end
    else if ( op == 4'( __const__ALU_SRL ) ) begin
      out = a >> b_sub;
    end
    else if ( op == 4'( __const__ALU_SLL ) ) begin
      out = a << b_sub;
    end
    else if ( op == 4'( __const__ALU_SRA ) ) begin
      if ( a[6'd32 - 6'd1] ) begin
        out = ( a >> b_sub ) | ( ~( 32'( __const__ONES_at_updt ) >> b_sub ) );
      end
      else
        out = a >> b_sub;
    end
    else if ( op == 4'( __const__ALU_SLT ) ) begin
      if ( a[6'd32 - 6'd1] ^ b[6'd32 - 6'd1] ) begin
        out = { { 31 { 1'b0 } }, a[6'd32 - 6'd1] };
      end
      else if ( a < b ) begin
        out = 32'd1;
      end
      else
        out = 32'd0;
    end
    else if ( op == 4'( __const__ALU_SLTU ) ) begin
      out = ( a < b ) ? 32'd1 : 32'd0;
    end
    else if ( op == 4'( __const__ALU_LUI_COPY ) ) begin
      out = a << 4'd12;
    end
    else
      out = 32'd0;
  end

endmodule
