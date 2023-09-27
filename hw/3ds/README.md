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

### parts

for disassembly I followed this guide for [3ds disassembly] carefull with:

- [JIS screwdrivers]  (don't use phillips!)
- [precision tweezers]
- [spudgers and opening tools]

[3ds disassembly]: https://www.ifixit.com/Guide/Nintendo+3DS+Motherboard+Replacement/6017
[JIS screwdrivers]: https://amzn.to/3sHk8Or
[precision tweezers]: https://amzn.to/45DjIY8
[spudgers]: https://amzn.to/3sHEdUO

for my assembly I used:

- [pro micro]
- [74LVC245 level shifter] (I had 0 luck with the TXS0108E)
- [32 AWG magnet wire]

[pro micro]: https://amzn.to/44Cxh8J
[74LVC245 level shifter]: https://amzn.to/3R7XZ64
[32 AWG magnet wire]: https://amzn.to/3R3LlVM

### 3ds testpoints

these are the ones I soldered to

```
TP1   GND
TP5   +1.8V
TP89  A
TP92  B
TP86  X
TP88  Y
TP85  up
TP87  left
TP91  down
TP90  right
TP83  L
TP82  R
TP80  start
TP81  select
TP55  home  # for next time
```

### wiring diagram

![](https://github.com/asottile/3ds-microcontroller/assets/1810591/d02344e2-5072-4d2c-b17f-9944de57c485)

it's quite difficult to see all of the wiring from the photo but here are the
connections:

- `+1.8V` from the 3ds connects to `DIR`, `Vcc` on the `74LVC245`
- `GND` from the 3ds is tied to `GND` from the microcontroller.  this is also
  tied to `GND` and `OE` on the `74LVC245`
- digital output pins from the microcontroller are connected to `A#` pins on
  the `74LVC245`
- leads to the corresponding testpoints are connected to the `B#` pins
- the datasheet recommends connecting unused `74LVC245` pins to `GND`
