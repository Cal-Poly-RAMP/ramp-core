//-------------------------------------------------------------------------
// MultiInputRdyCircularBuffer.v
//-------------------------------------------------------------------------
// This file is generated by PyMTL SystemVerilog translation pass.

// PyMTL Component MultiInputRdyCircularBuffer Definition
// Full name: MultiInputRdyCircularBuffer__Type_Bits32__size_16__num_inports_2
// At /Users/curtisbucher/Desktop/ramp-core/src/cl/buffers.py

module MultiInputRdyCircularBuffer
(
  input  logic [0:0] clk ,
  output logic [4:0] n_elements ,
  input  logic [0:0] reset ,
  output logic [3:0] tail ,
  input logic [0:0] allocate_in__en  ,
  input logic [4:0] allocate_in__msg  ,
  output logic [0:0] allocate_in__rdy  ,
  output logic [0:0] out__en  ,
  output logic [31:0] out__msg  ,
  input logic [0:0] out__rdy  ,
  input logic [0:0] update_idx_in__en [0:1] ,
  input logic [3:0] update_idx_in__msg [0:1] ,
  output logic [0:0] update_idx_in__rdy [0:1] ,
  input logic [0:0] update_in__en [0:1] ,
  input logic [31:0] update_in__msg [0:1] ,
  output logic [0:0] update_in__rdy [0:1] 
);
  localparam logic [4:0] __const__size_at_updt_comb  = 5'd16;
  localparam logic [31:0] __const__type_reset_val_at_updt_comb  = 32'd0;
  localparam logic [1:0] __const__num_inports_at_updt_comb  = 2'd2;
  localparam logic [1:0] __const__num_inports_at_updt_ff  = 2'd2;
  logic [31:0] buffer [0:15];
  logic [0:0] buffer_rdy [0:15];
  logic [0:0] empty;
  logic [0:0] full;
  logic [3:0] head;
  logic [3:0] head_next;
  logic [4:0] n_elements_next;
  logic [0:0] out_en_next;
  logic [31:0] out_next;
  logic [3:0] tail_next;

  // PyMTL Update Block Source
  // At /Users/curtisbucher/Desktop/ramp-core/src/cl/buffers.py:56
  // @update
  // def updt_comb():
  //     s.full @= s.n_elements == size
  //     s.empty @= s.n_elements == 0
  //     s.allocate_in.rdy @= ~s.full
  // 
  //     # reset
  //     if s.reset:
  //         s.out_next @= type_reset_val
  //         s.head_next @= 0
  //         s.tail_next @= 0
  //         s.n_elements_next @= 0
  //     else:
  //         # default values
  //         s.out_en_next @= 0
  //         s.head_next @= s.head
  //         s.tail_next @= s.tail
  //         s.n_elements_next @= s.n_elements
  // 
  //         # popping off stack if first element valid
  //         if s.out.rdy & ~s.empty:
  //             # checking head of stack
  //             if s.buffer_rdy[s.head]:
  //                 s.out_next @= s.buffer[s.head]
  //                 s.out_en_next @= 1
  //                 s.head_next @= s.head_next + 1
  //                 s.n_elements_next @= s.n_elements - 1
  //             # forwarding update inputs
  //             for i in range(num_inports):
  //                 # ensuring that update data has a corresponding index
  //                 # TODO: CL debugging
  //                 # assert ~(s.update_idx_in[i].en ^ s.update_in[i].en)
  //                 if s.update_idx_in[i].en & (s.update_idx_in[i].msg == s.head):
  //                     # checking that index has valid corresponding data
  //                     s.out_next @= s.update_in[i].msg
  //                     s.out_en_next @= 1
  //                     s.head_next @= s.head_next + 1
  //                     s.n_elements_next @= s.n_elements - 1
  // 
  //         # updating tail with elements allocated
  //         if s.allocate_in.en == 1:
  //             s.tail_next @= trunc(
  //                 zext(s.tail, s.n_elements_nbits) + s.allocate_in.msg,
  //                 s.tail_nbits
  //             )
  //             s.n_elements_next @= s.n_elements_next + zext(
  //                 s.allocate_in.msg,
  //                 s.n_elements_nbits
  //             )
  
  always_comb begin : updt_comb
    full = n_elements == 5'( __const__size_at_updt_comb );
    empty = n_elements == 5'd0;
    allocate_in__rdy = ~full;
    if ( reset ) begin
      out_next = 32'( __const__type_reset_val_at_updt_comb );
      head_next = 4'd0;
      tail_next = 4'd0;
      n_elements_next = 5'd0;
    end
    else begin
      out_en_next = 1'd0;
      head_next = head;
      tail_next = tail;
      n_elements_next = n_elements;
      if ( out__rdy & ( ~empty ) ) begin
        if ( buffer_rdy[head] ) begin
          out_next = buffer[head];
          out_en_next = 1'd1;
          head_next = head_next + 4'd1;
          n_elements_next = n_elements - 5'd1;
        end
        for ( int unsigned i = 1'd0; i < 2'( __const__num_inports_at_updt_comb ); i += 1'd1 )
          if ( update_idx_in__en[1'(i)] & ( update_idx_in__msg[1'(i)] == head ) ) begin
            out_next = update_in__msg[1'(i)];
            out_en_next = 1'd1;
            head_next = head_next + 4'd1;
            n_elements_next = n_elements - 5'd1;
          end
      end
      if ( allocate_in__en == 1'd1 ) begin
        tail_next = 4'({ { 1 { 1'b0 } }, tail } + allocate_in__msg);
        n_elements_next = n_elements_next + allocate_in__msg;
      end
    end
  end

  // PyMTL Update Block Source
  // At /Users/curtisbucher/Desktop/ramp-core/src/cl/buffers.py:106
  // @update_ff
  // def updt_ff():
  //     # reset
  //     # TODO: just set the first ready bit to 0?
  //     if s.reset:
  //         for i in range(num_inports):
  //             s.buffer_rdy[i] <<= 0
  // 
  //     # setting newely allocated elements to 0
  //     # if s.allocate_in.en:
  //     #     for i in range(num_inports):
  //     #         if (i > s.tail_next) & (i < s.head_next):
  //     #             s.buffer_rdy[i] <<= 0
  // 
  //     # updating data, and setting ready bit
  //     for i in range(num_inports):
  //         # ensuring that update data has a corresponding index
  //         # TODO: CL debugging
  //         # assert ~(
  //         #     s.update_idx_in[i].en ^ s.update_in[i].en
  //         # ), f"update idx[{i}] en: {s.update_idx_in[i].en}, update[{i}] en: {s.update_in[i].en}"
  //         if s.update_idx_in[i].en:
  //             s.buffer[s.update_idx_in[i].msg] <<= s.update_in[i].msg
  //             s.buffer_rdy[s.update_idx_in[i].msg] <<= 1
  // 
  //     # updating state
  //     s.tail <<= s.tail_next
  //     s.head <<= s.head_next
  //     s.out.msg <<= s.out_next
  //     s.out.en <<= s.out_en_next
  //     s.n_elements <<= s.n_elements_next
  
  always_ff @(posedge clk) begin : updt_ff
    if ( reset ) begin
      for ( int unsigned i = 1'd0; i < 2'( __const__num_inports_at_updt_ff ); i += 1'd1 )
        buffer_rdy[4'(i)] <= 1'd0;
    end
    for ( int unsigned i = 1'd0; i < 2'( __const__num_inports_at_updt_ff ); i += 1'd1 )
      if ( update_idx_in__en[1'(i)] ) begin
        buffer[update_idx_in__msg[1'(i)]] <= update_in__msg[1'(i)];
        buffer_rdy[update_idx_in__msg[1'(i)]] <= 1'd1;
      end
    tail <= tail_next;
    head <= head_next;
    out__msg <= out_next;
    out__en <= out_en_next;
    n_elements <= n_elements_next;
  end

  assign update_in__rdy[0] = 1'd1;
  assign update_idx_in__rdy[0] = 1'd1;
  assign update_in__rdy[1] = 1'd1;
  assign update_idx_in__rdy[1] = 1'd1;

endmodule
