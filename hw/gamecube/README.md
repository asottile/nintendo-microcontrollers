gamecube-microcontroller
========================

### wiring

- [pro micro](https://amzn.to/3ROYsuu)
- [logic level converter](https://amzn.to/3RHQAe6)

I'm using a stock gamecube cable:

_3rd party may be different so test with a multimeter_

- red: data (3.3v)
- blue: supply (3.3v)
- green: ground (3.3v)
- yellow: supply (5v) _(left not connected)_
- white: ground (5v) _(left not connected)_

a 1k resistor pulls up 3.3v data to supply

the red magnet wire is soldered to pins 1 and 2 of the wii reset button.
you will need to [disassemble the wii] to do this (up to step 22, plus step 32).

[disassemble the wii]: https://www.ifixit.com/Guide/Nintendo+Wii+Motherboard+Replacement/3460

![](https://user-images.githubusercontent.com/1810591/273344828-1895eab3-26d1-400c-85f0-54a6e0e69b27.jpg)
