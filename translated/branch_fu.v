//-------------------------------------------------------------------------
// BranchFU.v
//-------------------------------------------------------------------------
// This file is generated by PyMTL SystemVerilog translation pass.

// PyMTL BitStruct BranchUpdate__target_32__mispredict_1__tag_3 Definition
typedef struct packed {
  logic [31:0] target;
  logic [0:0] mispredict;
  logic [2:0] tag;
} BranchUpdate__target_32__mispredict_1__tag_3;

// PyMTL BitStruct MicroOp__38e2b09b91e4b306 Definition
typedef struct packed {
  logic [2:0] optype;
  logic [31:0] inst;
  logic [31:0] pc;
  logic [0:0] valid;
  logic [4:0] lrd;
  logic [4:0] lrs1;
  logic [4:0] lrs2;
  logic [5:0] prd;
  logic [5:0] prs1;
  logic [5:0] prs2;
  logic [5:0] stale;
  logic [31:0] imm;
  logic [1:0] issue_unit;
  logic [1:0] funct_unit;
  logic [3:0] funct_op;
  logic [0:0] branch_taken;
  logic [7:0] br_mask;
  logic [2:0] br_tag;
  logic [4:0] rob_idx;
  logic [3:0] mem_q_idx;
} MicroOp__38e2b09b91e4b306;

// PyMTL Component BranchFU Definition
// Full name: BranchFU_noparam
// At /Users/curtisbucher/Desktop/ramp-core/src/cl/branch_fu.py

module BranchFU
(
  input  logic [0:0] clk ,
  input  logic [0:0] reset ,
  input  logic [31:0] rs1_din ,
  input  logic [31:0] rs2_din ,
  input  MicroOp__38e2b09b91e4b306 uop ,
  output logic [0:0] br_update__en  ,
  output BranchUpdate__target_32__mispredict_1__tag_3 br_update__msg  ,
  input logic [0:0] br_update__rdy  
);
  localparam logic [1:0] __const__BRANCH_FUNCT_UNIT  = 2'd3;
  localparam logic [3:0] __const__BFU_BEQ  = 4'd0;
  localparam logic [3:0] __const__BFU_BNE  = 4'd1;
  localparam logic [3:0] __const__BFU_BLT  = 4'd4;
  localparam logic [3:0] __const__BFU_BGE  = 4'd5;
  localparam logic [3:0] __const__BFU_BLTU  = 4'd6;
  localparam logic [3:0] __const__BFU_BGEU  = 4'd7;
  logic [0:0] __tmpvar__updt_rs1_neg;
  logic [0:0] __tmpvar__updt_rs2_neg;
  logic [0:0] __tmpvar__updt_sign_diff;

  // PyMTL Update Block Source
  // At /Users/curtisbucher/Desktop/ramp-core/src/cl/branch_fu.py:29
  // @update
  // def updt():
  //     # for signed logic
  //     rs1_neg = s.rs1_din[32 - 1]
  //     rs2_neg = s.rs2_din[32 - 1]
  //     sign_diff = rs1_neg ^ rs2_neg
  //     s.br_update.en @= s.uop.funct_unit == BRANCH_FUNCT_UNIT
  //     s.br_update.msg.tag @= s.uop.br_tag
  // 
  //     # if branch taken...
  //     if (
  //         ((s.uop.funct_op == BFU_BEQ) & (s.rs1_din == s.rs2_din))
  //         | ((s.uop.funct_op == BFU_BNE) & (s.rs1_din != s.rs2_din))
  //         | (
  //             (s.uop.funct_op == BFU_BLT)
  //             & ((sign_diff & rs1_neg) | (~sign_diff & (s.rs1_din < s.rs2_din)))
  //         )
  //         | (
  //             (s.uop.funct_op == BFU_BGE)
  //             & ((sign_diff & rs2_neg) | (~sign_diff & (s.rs1_din >= s.rs2_din)))
  //         )
  //         | ((s.uop.funct_op == BFU_BLTU) & (s.rs1_din < s.rs2_din))
  //         | ((s.uop.funct_op == BFU_BGEU) & (s.rs1_din >= s.rs2_din))
  //     ):
  // 
  //         # mispredict if branch is predicted not taken but taken
  //         s.br_update.msg.mispredict @= ~s.uop.branch_taken
  //         s.br_update.msg.target @= s.uop.pc + s.uop.imm
  // 
  //     # if branch not taken...
  //     else:
  //         # mispredict if branch is predicted taken but not taken
  //         s.br_update.msg.mispredict @= s.uop.branch_taken
  //         s.br_update.msg.target @= s.uop.pc + 8
  
  always_comb begin : updt
    __tmpvar__updt_rs1_neg = rs1_din[6'd32 - 6'd1];
    __tmpvar__updt_rs2_neg = rs2_din[6'd32 - 6'd1];
    __tmpvar__updt_sign_diff = __tmpvar__updt_rs1_neg ^ __tmpvar__updt_rs2_neg;
    br_update__en = uop.funct_unit == 2'( __const__BRANCH_FUNCT_UNIT );
    br_update__msg.tag = uop.br_tag;
    if ( ( ( ( ( ( ( uop.funct_op == 4'( __const__BFU_BEQ ) ) & ( rs1_din == rs2_din ) ) | ( ( uop.funct_op == 4'( __const__BFU_BNE ) ) & ( rs1_din != rs2_din ) ) ) | ( ( uop.funct_op == 4'( __const__BFU_BLT ) ) & ( ( __tmpvar__updt_sign_diff & __tmpvar__updt_rs1_neg ) | ( ( ~__tmpvar__updt_sign_diff ) & ( rs1_din < rs2_din ) ) ) ) ) | ( ( uop.funct_op == 4'( __const__BFU_BGE ) ) & ( ( __tmpvar__updt_sign_diff & __tmpvar__updt_rs2_neg ) | ( ( ~__tmpvar__updt_sign_diff ) & ( rs1_din >= rs2_din ) ) ) ) ) | ( ( uop.funct_op == 4'( __const__BFU_BLTU ) ) & ( rs1_din < rs2_din ) ) ) | ( ( uop.funct_op == 4'( __const__BFU_BGEU ) ) & ( rs1_din >= rs2_din ) ) ) begin
      br_update__msg.mispredict = ~uop.branch_taken;
      br_update__msg.target = uop.pc + uop.imm;
    end
    else begin
      br_update__msg.mispredict = uop.branch_taken;
      br_update__msg.target = uop.pc + 32'd8;
    end
  end

endmodule
