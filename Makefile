# --cov-report=html, -n auto
test:
	pytest --cov=src --cov-branch --cov-report=term-missing --cov-fail-under=90

# not working rn, only works with io from ramp-core
test-verilog:
	pytest tests/test_ramp_core.py --test-verilog --cov=src --cov-branch --cov-report=term-missing --cov-fail-under=90; rm -r *RampCore__*

# Test in Python
format:
	black src/*/*.py tests/*.py

synthesis:
	python synthesize.py

#removing translated files, logfiles.
clean:
	rm translated/* ; rm vcd/* ;

# cleaning up verilator files
clean-verilator:
	 rm -r *RampCore__* ;

.PHONY: test test-verilog synthesis
