# Ramp Core
***In Progress***

RAMP's out-of-order RV32G processor core implemented with the [PyMTL3](https://pymtl.github.io) framework.

Repository working on Ubuntu, finnicky on Mac, untested on Windows.

## Quickstart
Download Repo:</br>
`$ git clone https://github.com/Cal-Poly-RAMP/ramp-core`

Install Requirements:</br>
`$ pip install -r requirements.txt`

Install [Verilator](https://www.veripool.org/verilator/) (Mac):</br>
`$ brew install verilator`

Install [Verilator](https://www.veripool.org/verilator/) (Ubuntu):</br>
`$ apt-get install verilator`

## Testing
Run test suite with pymtl:</br> 
`$ make test` or</br> 
`$ pytest tests/*`

Run test suite with verilator:</br>
`$ make test-verilog` or </br> 
`$ pytest tests/* --test-verilog`

## Synthesis
Compile PyMTL code into SystemVerilog, under `translated/`:</br>
`$ make synthesis` or</br> 
`$ python synthesis.py`
