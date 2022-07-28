# Test in Python
format:
	black src/*/*.py tests/*.py

test:
	python -m pytest

# Test verilog source
# test-verilog : synthesis
# 	verilator -cc

synthesis:
	mkdir translated
	python synthesize.py

.PHONY: test test-verilog synthesis
