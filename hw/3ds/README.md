3ds-microcontroller
===================

### setup

on ubuntu I needed the following packages:

```bash
sudo apt install arduino-core-avr avr-libc avrdude gcc-avr
```

### configure

set `AVRDIR` in the makefile if yours is different

set `VARIANT` in the makefile if yours is different.  _hint_:

```bash
ls /usr/share/arduino/hardware/arduino/avr/variants/
```

### build

```bash
make -j5
```

### flashing

you have to be quick with this!

- connect the pro micro to your computer
- short `rst` to `gnd` twice in quick succession

```bash
sudo avrdude -v -patmega32u4 -cavr109 -P/dev/ttyACM0 -Uflash:w:main.hex
```

use the appropriate `MCU` and serial port for your board, the pro micro uses
`atmega32u4` and `/dev/ttyACM0`
