import traceback

from pymtl3 import *
from pymtl3.passes.backends.verilog import *

from src.cl import (
    decoder,
    dispatch,
    fetch_stage,
    front_end,
    icache,
    memory,
    ramp_core,
    register_rename,
    reorder_buffer,
    issue_queue,
    alu,
)

import os

GREEN = "\x1B[32m"
RED = "\x1B[31m"
END = "\u001b[0m"

# Synthesize a model
def synthesize(model):
    # Set metadata
    filename = "./translated/" + model.__module__.split(".")[-1]
    model.set_metadata(VerilogTranslationPass.enable, True)
    model.set_metadata(
        VerilogTranslationPass.explicit_file_name,
        filename,
    )
    model.set_metadata(
        VerilogTranslationPass.explicit_module_name, model.__class__.__name__
    )

    # Generate Verilog
    model.apply(VerilogTranslationPass())

    return  filename

if __name__ == "__main__":
    models = [
        ramp_core.RampCore(),
        decoder.Decode(),
        dispatch.Dispatch(),
        fetch_stage.FetchStage(),
        front_end.FrontEnd(),
        # icache.ICache(),
        # memory.Memory(),
        register_rename.RegisterRename(),
        reorder_buffer.ReorderBuffer(),
        issue_queue.IssueQueue(),
        alu.ALU(mk_bits(32)),
    ]
    failed = []
    size = os.get_terminal_size().columns

    msg = "Synthesizing"
    print(f"{'='*((size-len(msg)-1)//2)} {msg} {'='*((size-len(msg)-1)//2)}")

    for model in models:
        try:
            model.elaborate()
            filename = synthesize(model)
            print(GREEN, model.__class__.__name__, "synthesized successfully:", filename + ".v", END)
        except Exception as e:
            print(RED, model.__class__.__name__, "synthesizing failed:", END)
            failed.append((model.__class__.__name__, traceback.format_exc(limit=-1)))
            continue

    msg = "Failures"
    print(f"{'='*((size-len(msg)-1)//2)} {msg} {'='*((size-len(msg)-1)//2)}")

    for f in failed:
        name, err = f
        print(f"{RED}{'_'*((size-len(name)-1)//2)} {name} {'_'*((size-len(name)-1)//2)}{END}")
        print(err)