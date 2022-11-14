
# ![LOGO](https://avatars.githubusercontent.com/u/110626682?s=75&u=07248cbe600c2763efdb240b7730736435d71ad7&v=4) Ramp Core
***In Progress*** | [Docs](https://ramp-core.readthedocs.io/en/latest/) | [Homepage](https://cal-poly-ramp.github.io/ramp-core/) |

RAMP's out-of-order RV32G processor core implemented with the [PyMTL3](https://pymtl.github.io) framework.

Repository working on Ubuntu, finnicky on Mac, untested on Windows.

## Quickstart
Download Repo: \
`$ git clone https://github.com/Cal-Poly-RAMP/ramp-core`

Install Requirements: \
`$ pip install -r requirements.txt`

Install [Verilator](https://www.veripool.org/verilator/) (Mac): \
`$ brew install verilator`

Install [Verilator](https://www.veripool.org/verilator/) (Ubuntu): \
`$ apt-get install verilator`

## Testing
Run test suite with pymtl: \
`$ make test` or \
`$ pytest tests/*`

Run test suite with verilator: \
`$ make test-verilog` or \
`$ pytest tests/* --test-verilog`

## Synthesis
Compile PyMTL code into SystemVerilog, under `translated/`: \
`$ make synthesis` or \
`$ python synthesis.py`

## Resources
[Presentation](https://github.com/Cal-Poly-RAMP/ramp-core/blob/9185850a935498318f1f76ee783e12f6f9012397/docs/source/Bucher,%20Callenes%20Poster.pdf) \
[Architecture Diagram](https://github.com/Cal-Poly-RAMP/ramp-core/blob/9185850a935498318f1f76ee783e12f6f9012397/docs/source/ramp-high-level-interface-printing.drawio.pdf)
