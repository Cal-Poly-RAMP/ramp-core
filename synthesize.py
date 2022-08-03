from pymtl3 import *
from pymtl3.passes.backends.verilog import *
from src.cl import decoder, fetch_stage, icache, memory, register_rename


# Synthesize a model
def synthesize(model):
    # Set metadata
    model.set_metadata(VerilogTranslationPass.enable, True)
    model.set_metadata(VerilogTranslationPass.explicit_file_name, "./translated/" + model.__module__.split(".")[-1])
    model.set_metadata(VerilogTranslationPass.explicit_module_name, model.__class__.__name__)

    # Generate Verilog
    model.apply( VerilogTranslationPass() )

if __name__ == "__main__":
    models = [decoder.SingleInstDecode(),
                decoder.Decode(),
                icache.ICache(),
                # memory.Memory(),
                register_rename.RegisterRename()
              ]

    for model in models:
        try:
            model.elaborate()
            synthesize(model)
            print(model.__class__.__name__, "synthesized successfully")
        except Exception as e:
            print(model.__class__.__name__, "synthesizing failed:", e)
            # if not str(e):
            #     raise(e)
            continue