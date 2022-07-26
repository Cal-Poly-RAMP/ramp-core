# Test in Python
test :
	python -m unittest tests/*.py

format:
	black src/*/*.py tests/*.py

# Test verilog source
# test-verilog : synthesis
# 	verilator -cc

synthesis:
	mkdir translated
	python synthesize.py

.PHONY: test test-verilog synthesis