from pymtl3 import (
    Component,
    InPort,
    OutPort,
    clog2,
    update,
    update_ff,
    Wire,
    mk_bits,
    Bits1,
)
from pymtl3.stdlib.ifcs import RecvIfcRTL, SendIfcRTL


class DRAM(Component):
    def construct(
        s, Type, num_entries=32, rd_ports=1, wr_ports=1, reset_value=0, data=None
    ):
        if data:
            assert len(data) == num_entries
        assert num_entries > 0

        addr_type = mk_bits(max(1, clog2(num_entries)))

        s.raddr = [InPort(addr_type) for _ in range(rd_ports)]
        s.rdata = [OutPort(Type) for _ in range(rd_ports)]

        s.waddr = [InPort(addr_type) for _ in range(wr_ports)]
        s.wdata = [InPort(Type) for _ in range(wr_ports)]
        s.wen = [InPort(Bits1) for _ in range(wr_ports)]

        s.mem = [Wire(Type) for _ in range(num_entries)]
        # Filling in memory with data if provided1
        if data:
            for i in range(num_entries):
                assert type(data[i]) == Type
                s.mem[i] //= data[i]

        @update
        def up_rf_read():
            for i in range(rd_ports):
                s.rdata[i] @= s.mem[s.raddr[i]]

        @update_ff
        def up_rf_write():
            if s.reset:
                for i in range(num_entries):
                    s.mem[i] <<= reset_value
            else:
                for i in range(wr_ports):
                    if s.wen[i]:
                        s.mem[s.waddr[i]] <<= s.wdata[i]

    def line_trace(s):
        return f"\nDRAM: {[e.uint() for e in s.mem]}"