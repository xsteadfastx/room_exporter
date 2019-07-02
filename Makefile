.PHONY: screen put

screen:
	picocom /dev/ttyUSB0 -b115200

put:
	ampy -p /dev/ttyUSB0 put main.py
