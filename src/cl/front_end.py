from pymtl3 import *
from src.cl.decoder import Decode
from src.cl.fetch_stage import FetchStage

class FrontEnd(Component):
    def construct(s):
        s.fetch_stage = FetchStage()

        s.decoder = Decode()
        s.decoder.fetch_packet //= s.fetch_stage.send.msg