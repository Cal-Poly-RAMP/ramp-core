# Responsible for allocating tags to branches, and branch masks for non-branches
from pymtl3 import Component, OutPort, clog2, update, update_ff, Wire
from pymtl3.stdlib.ifcs import RecvIfcRTL, SendIfcRTL

# TODO: should be able two back-to-back branches
class BranchAllocate(Component):
    def construct(s, ntags=8):
        # The branch tag for the next branch to be decoded
        s.next_branch_tag = SendIfcRTL(clog2(ntags))
        s.br_mask = OutPort(ntags)
        s.br_mask_next = Wire(ntags)

        s.deallocate_tag = RecvIfcRTL(clog2(ntags))

        @update_ff
        def updt_ff():
            if s.reset:
                s.br_mask <<= 0
            else:
                s.br_mask <<= s.br_mask_next

        @update
        def updt():
            # deallocate executed branch
            if s.deallocate_tag.en:
                s.br_mask_next @= s.br_mask & ~(1 << s.deallocate_tag.msg)
            else:
                s.br_mask_next @= s.br_mask

            # allocate the first available bit in br_mask, if available
            s.next_branch_tag.en @= 0
            for i in range(ntags - 1, -1, -1):
                if s.br_mask_next[i] == 0:
                    s.next_branch_tag.en @= 1
                    s.next_branch_tag.msg @= i

            # if a branch was allocated, update branch mask
            if s.next_branch_tag.en:
                s.br_mask_next @= s.br_mask_next | (1 << s.next_branch_tag.msg)

    def line_trace(s):
        return (f"BranchAllocate:\nnext_branch_tag={s.next_branch_tag.msg}"
                f"\nbr_mask={s.br_mask}")