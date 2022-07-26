from pymtl3 import *
from pymtl3.passes.backends.verilog import *

from src.alu import ALU
from src.branch_addr_gen import BranchAddrGen
from src.branch_cond_gen import BranchCondGen
from src.cs_registers import CSRegisters
from src.cu_decoder import CUDecoder
from src.otter_mem import Memory


# Synthesize a model
def synthesize(model):
    # Set metadata
    model.set_metadata(VerilogTranslationPass.enable, True)
    model.set_metadata(VerilogTranslationPass.explicit_file_name, "./translated/" + model.__module__.split(".")[-1])
    model.set_metadata(VerilogTranslationPass.explicit_module_name, model.__class__.__name__)

    # Generate Verilog
    model.apply( VerilogTranslationPass() )

if __name__ == "__main__":
    models = [ALU(32),
              BranchAddrGen(32),
              BranchCondGen(32),
              CSRegisters(32),
              CUDecoder(32),
              Memory(32)]

    for model in models:
        print("Synthesizing model: " + model.__class__.__name__)
        try:
            synthesize(model)
        except Exception as e:
            print("Error: " + str(e))
            continue
        print("Done")