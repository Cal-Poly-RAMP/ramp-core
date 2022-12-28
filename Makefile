# --cov-report=html, -n auto
test:
	python -m pytest --cov=src --cov-branch --cov-report=term-missing --cov-fail-under=90

# Test in Python
format:
	black src/*/*.py tests/*.py

# Test verilog source
# test-verilog : synthesis
# 	verilator -cc

synthesis:
	python synthesize.py

test-synthesis:
	make synthesis
	make clean

clean:
	rm translated/* & rm vcd/*

.PHONY: test test-verilog synthesis
