# Responsible for allocating tags to branches, and branch masks for non-branches
from pymtl3 import Component, OutPort, clog2, update, update_ff, Wire
from pymtl3.stdlib.ifcs import RecvIfcRTL, SendIfcRTL

# TODO: should be able two back-to-back branches
class BranchAllocate(Component):
    def construct(s, ntags=8, window_size=2):
        # The branch tag for the next branch to be decoded
        s.br_tag = [SendIfcRTL(clog2(ntags)) for _ in range(window_size)]
        s.br_mask = [OutPort(ntags) for _ in range(window_size)]

        s.br_freelist = Wire(ntags)
        s.br_freelist_next = Wire(ntags)

        s.deallocate_tag = RecvIfcRTL(clog2(ntags))

        @update_ff
        def updt_ff():
            if s.reset:
                s.br_freelist <<= 0
            else:
                s.br_freelist <<= s.br_freelist_next

        @update
        def updt():
            # deallocate executed branch
            # breakpoint()
            s.br_freelist_next @= s.br_freelist
            if s.deallocate_tag.en:
                s.br_freelist_next[s.deallocate_tag.msg] @= 0

            # allocate the first available bit in br_mask, if available
            # update freelist accordingly
            for i in range(window_size):
                s.br_tag[i].en @= 0
                s.br_tag[i].msg @= 0
                s.br_mask[i] @= s.br_freelist_next
                for b in range(ntags):
                    if (s.br_freelist_next[b] == 0) & s.br_tag[i].rdy:
                        s.br_tag[i].en @= 1
                        s.br_tag[i].msg @= b
                        s.br_freelist_next[s.br_tag[i].msg] @= 1
                        break

    def line_trace(s):
        return (f"BranchAllocate:\n"
                f"br_freelist: {s.br_freelist}\n"
                f"br_freelist_next: {s.br_freelist_next}\n"
                f"br_mask: {[e for e in s.br_mask]}\n"
                f"br_tag_rdy: {[e.rdy for e in s.br_tag]}\n"
                f"br_tag: {[e.msg if e.en else '-' for e in s.br_tag]}\n"
                f"deallocate_tag: {s.deallocate_tag.msg if s.deallocate_tag.en else '-'}\n")