AVRDIR = /usr/share/arduino/hardware/arduino/avr
VARIANT = micro

# ---

SHELL := /bin/bash

_CONF := $(AVRDIR)/boards.txt
_CORE := $(AVRDIR)/cores/arduino

_MCU := $(shell grep "^$(VARIANT).build.mcu=" "$(_CONF)" | cut -d= -f2)
_F_CPU := $(shell grep "^$(VARIANT).build.f_cpu=" "$(_CONF)" | cut -d= -f2)

_AVR_S := $(wildcard $(_CORE)/*.S)
_AVR_S_O := $(notdir $(_AVR_S:.S=.S.o))

_AVR_C := $(wildcard $(_CORE)/*.c)
_AVR_C_O := $(notdir $(_AVR_C:.c=.c.o))

_AVR_CPP := $(wildcard $(_CORE)/*.cpp)
_AVR_CPP_O := $(notdir $(_AVR_CPP:.cpp=.cpp.o))
# do not use arduino's main.cpp
_AVR_CPP_O := $(filter-out main.cpp.o,$(_AVR_CPP_O))

_OBJECTS = $(addprefix out/,main.cpp.o $(_AVR_S_O) $(_AVR_C_O) $(_AVR_CPP_O))

CFLAGS := \
    -Os \
    -DF_CPU=$(_F_CPU) \
    -DUSB_VID=0xbaad \
    -DUSB_PID=0xf00d \
    -mmcu=$(_MCU) \
    -I$(_CORE) \
    -I$(AVRDIR)/variants/$(VARIANT)

CXXFLAGS := \
    -std=c++11 \
    -fno-threadsafe-statics

.PHONY: all
all: main.hex

out:
	mkdir out

out/main.cpp.o: main.cpp | out
	avr-gcc -c $(CFLAGS) $(CXXFLAGS) -o $@ $<

out/%.S.o: $(_CORE)/%.S | out
	avr-gcc -c $(CFLAGS) -o $@ $<

out/%.c.o: $(_CORE)/%.c | out
	avr-gcc -c $(CFLAGS) -o $@ $<

out/%.cpp.o: $(_CORE)/%.cpp | out
	avr-gcc -c $(CFLAGS) $(CXXFLAGS) -o $@ $<

out/main.elf: $(_OBJECTS) | out
	avr-gcc $(CFLAGS) $^ -o $@

main.hex: out/main.elf | out
	avr-objcopy -O ihex $< $@

.PHONY: clean
clean:
	rm -rf main.hex out/
