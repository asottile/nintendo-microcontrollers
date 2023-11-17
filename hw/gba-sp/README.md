gba-sp
======

### gba sp testpoints

```
TP0    A
TP1    B
TP2    select
TP3    start
TP4    right
TP5    left
TP6    up
TP7    down
TP8    R
TP9    L
RESET  reset
```

there's lots of choices for ground.  I used the GND for the R button contacts

### wiring

![](https://user-images.githubusercontent.com/1810591/283647355-d76345d8-798c-4357-a7bf-8ae44b05d2d8.jpg)

I have some additional wires soldered because I initially thought I'd need to
fake the power switch (before discovering the `RESET` pad!).

I'm using the `INPUT` / `OUTPUT` trick to fake "shorting to GND".
