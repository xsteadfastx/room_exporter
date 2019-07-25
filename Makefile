.PHONY: shell put

shell:
	mpfshell ttyUSB0

put:
	ampy -p /dev/ttyUSB0 put main.py
