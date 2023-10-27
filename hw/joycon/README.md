joycon
======

generally you'll want to use the [switch](../switch) controller instead --
unless your game requires a joycon (such as pokemon let's go).

![](https://user-images.githubusercontent.com/1810591/278831913-0750550a-4dcf-4af3-a926-f26d6868b54c.jpg)

### wiring

I mostly followed these resources:

- [dekuNukem/Nintendo_Switch_Reverse_Engineering](https://github.com/dekuNukem/Nintendo_Switch_Reverse_Engineering)
- [moribellamy/porygon](https://github.com/moribellamy/porygon)

there is no pin for `HOME` so I soldered directly to the button.  it also
participates in the keypad layout described in dekuNukem's repo

I used [CD3066BE](https://amzn.to/40d10EM) chips to switch the buttons and
[MCP4725](https://amzn.to/3Fxmnap) for the analog stick.

the MCP4725 will need some calibration with a multimeter -- idk why they aren't
super accurate but on startup they should be at .8V.

I did not have a sufficient 5V source from my arduino so I cut up a USB cable
and connected that to pin 4 and pin 1 on the joycon to power it without
battery (the black and red wires pictured).
