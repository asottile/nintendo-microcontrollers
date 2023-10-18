3ds-touch
=========

similar to [3ds](../3ds) but with the ability to use the touch screen!

![](https://user-images.githubusercontent.com/1810591/276076967-36959b4e-5ebe-4bbc-8ded-9731c9005b8d.jpg)

### wiring

the main differences to the original 3ds mod are:

wires are soldered to Y+ and X+ on the touch screen.  due to a bunch of
debugging I soldered to a connector (pictured) though you should be able to
solder to the test points directly.  they should be TP213 and TP214.
more details @ [dekuNukem/3xtDS].

two DACs are connected to the i2c bus.  I used Adafruit's [MCP4725].

[dekuNukem/3xtDS]: https://github.com/dekuNukem/3xtDS
[MCP4725]: https://amzn.to/3PZrTY0
