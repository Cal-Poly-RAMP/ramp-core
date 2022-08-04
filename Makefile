# --cov-report=html, -n auto
test:
	python -m pytest --cov=src --cov-branch --cov-report=term-missing --cov-fail-under=96

# Test in Python
format:
	black src/*/*.py tests/*.py

# Test verilog source
# test-verilog : synthesis
# 	verilator -cc

synthesis:
	mkdir translated
	python synthesize.py

.PHONY: test test-verilog synthesis
