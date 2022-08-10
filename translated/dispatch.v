//-------------------------------------------------------------------------
// Dispatch.v
//-------------------------------------------------------------------------
// This file is generated by PyMTL SystemVerilog translation pass.

// PyMTL BitStruct MicroOp__8aebb2d496e39e44 Definition
typedef struct packed {
  logic [2:0] type;
  logic [31:0] inst;
  logic [7:0] pc;
  logic [0:0] valid;
  logic [4:0] lrd;
  logic [4:0] lrs1;
  logic [4:0] lrs2;
  logic [5:0] prd;
  logic [5:0] prs1;
  logic [5:0] prs2;
  logic [5:0] stale;
  logic [0:0] prs1_busy;
  logic [0:0] prs2_busy;
  logic [31:0] imm;
  logic [1:0] issue_unit;
  logic [1:0] fu_unit;
  logic [1:0] fu_op;
  logic [4:0] rob_idx;
} MicroOp__8aebb2d496e39e44;

// PyMTL BitStruct DualMicroOp__225a29605d3739d4 Definition
typedef struct packed {
  MicroOp__8aebb2d496e39e44 uop1;
  MicroOp__8aebb2d496e39e44 uop2;
} DualMicroOp__225a29605d3739d4;

// PyMTL Component SingleDispatch Definition
// At /Users/curtisbucher/Desktop/ramp-core/src/cl/dispatch.py

module SingleDispatch_noparam
(
  input  logic [0:0] clk ,
  input  MicroOp__8aebb2d496e39e44 in_ ,
  input  logic [0:0] reset ,
  input  logic [4:0] rob_idx ,
  output MicroOp__8aebb2d496e39e44 to_int_issue ,
  output MicroOp__8aebb2d496e39e44 to_mem_issue ,
  output MicroOp__8aebb2d496e39e44 to_rob 
);
  localparam logic [0:0] __const__INT_ISSUE_UNIT  = 1'd1;
  localparam logic [127:0] __const__NO_OP  = 128'd0;
  localparam logic [1:0] __const__MEM_ISSUE_UNIT  = 2'd2;

  // PyMTL Update Block Source
  // At /Users/curtisbucher/Desktop/ramp-core/src/cl/dispatch.py:58
  // @update
  // def issue():
  //     if s.in_.issue_unit == INT_ISSUE_UNIT:
  //         s.to_int_issue @= s.in_
  //         s.to_int_issue.rob_idx @= s.rob_idx
  //     else:
  //         s.to_int_issue @= NO_OP
  //     if s.in_.issue_unit == MEM_ISSUE_UNIT:
  //         s.to_mem_issue @= s.in_
  //         s.to_mem_issue.rob_idx @= s.rob_idx
  //     else:
  //         s.to_mem_issue @= NO_OP
  
  always_comb begin : issue
    if ( in_.issue_unit == 2'( __const__INT_ISSUE_UNIT ) ) begin
      to_int_issue = in_;
      to_int_issue.rob_idx = rob_idx;
    end
    else
      to_int_issue = 128'( __const__NO_OP );
    if ( in_.issue_unit == 2'( __const__MEM_ISSUE_UNIT ) ) begin
      to_mem_issue = in_;
      to_mem_issue.rob_idx = rob_idx;
    end
    else
      to_mem_issue = 128'( __const__NO_OP );
  end

  assign to_rob = in_;

endmodule


// PyMTL Component Dispatch Definition
// Full name: Dispatch_noparam
// At /Users/curtisbucher/Desktop/ramp-core/src/cl/dispatch.py

module Dispatch
(
  input  logic [0:0] clk ,
  input  DualMicroOp__225a29605d3739d4 in_ ,
  input  logic [0:0] reset ,
  input  logic [4:0] rob_idx ,
  output DualMicroOp__225a29605d3739d4 to_int_issue ,
  output DualMicroOp__225a29605d3739d4 to_mem_issue ,
  output DualMicroOp__225a29605d3739d4 to_rob 
);
  //-------------------------------------------------------------
  // Component uop1_dispatch
  //-------------------------------------------------------------

  logic [0:0] uop1_dispatch__clk;
  MicroOp__8aebb2d496e39e44 uop1_dispatch__in_;
  logic [0:0] uop1_dispatch__reset;
  logic [4:0] uop1_dispatch__rob_idx;
  MicroOp__8aebb2d496e39e44 uop1_dispatch__to_int_issue;
  MicroOp__8aebb2d496e39e44 uop1_dispatch__to_mem_issue;
  MicroOp__8aebb2d496e39e44 uop1_dispatch__to_rob;

  SingleDispatch_noparam uop1_dispatch
  (
    .clk( uop1_dispatch__clk ),
    .in_( uop1_dispatch__in_ ),
    .reset( uop1_dispatch__reset ),
    .rob_idx( uop1_dispatch__rob_idx ),
    .to_int_issue( uop1_dispatch__to_int_issue ),
    .to_mem_issue( uop1_dispatch__to_mem_issue ),
    .to_rob( uop1_dispatch__to_rob )
  );

  //-------------------------------------------------------------
  // End of component uop1_dispatch
  //-------------------------------------------------------------

  //-------------------------------------------------------------
  // Component uop2_dispatch
  //-------------------------------------------------------------

  logic [0:0] uop2_dispatch__clk;
  MicroOp__8aebb2d496e39e44 uop2_dispatch__in_;
  logic [0:0] uop2_dispatch__reset;
  logic [4:0] uop2_dispatch__rob_idx;
  MicroOp__8aebb2d496e39e44 uop2_dispatch__to_int_issue;
  MicroOp__8aebb2d496e39e44 uop2_dispatch__to_mem_issue;
  MicroOp__8aebb2d496e39e44 uop2_dispatch__to_rob;

  SingleDispatch_noparam uop2_dispatch
  (
    .clk( uop2_dispatch__clk ),
    .in_( uop2_dispatch__in_ ),
    .reset( uop2_dispatch__reset ),
    .rob_idx( uop2_dispatch__rob_idx ),
    .to_int_issue( uop2_dispatch__to_int_issue ),
    .to_mem_issue( uop2_dispatch__to_mem_issue ),
    .to_rob( uop2_dispatch__to_rob )
  );

  //-------------------------------------------------------------
  // End of component uop2_dispatch
  //-------------------------------------------------------------

  // PyMTL Update Block Source
  // At /Users/curtisbucher/Desktop/ramp-core/src/cl/dispatch.py:34
  // @update
  // def update_rob_idx():
  //     s.uop1_dispatch.rob_idx @= s.rob_idx
  //     s.uop2_dispatch.rob_idx @= s.rob_idx + 1
  
  always_comb begin : update_rob_idx
    uop1_dispatch__rob_idx = rob_idx;
    uop2_dispatch__rob_idx = rob_idx + 5'd1;
  end

  assign uop1_dispatch__clk = clk;
  assign uop1_dispatch__reset = reset;
  assign uop1_dispatch__in_ = in_.uop1;
  assign to_rob.uop1 = uop1_dispatch__to_rob;
  assign to_int_issue.uop1 = uop1_dispatch__to_int_issue;
  assign to_mem_issue.uop1 = uop1_dispatch__to_mem_issue;
  assign uop2_dispatch__clk = clk;
  assign uop2_dispatch__reset = reset;
  assign uop2_dispatch__in_ = in_.uop2;
  assign to_rob.uop2 = uop2_dispatch__to_rob;
  assign to_int_issue.uop2 = uop2_dispatch__to_int_issue;
  assign to_mem_issue.uop2 = uop2_dispatch__to_mem_issue;

endmodule
