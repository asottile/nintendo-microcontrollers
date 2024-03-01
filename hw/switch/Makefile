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

_HID := $(AVRDIR)/libraries/HID/src
_HID_CPP := $(wildcard $(_HID)/*.cpp)
_HID_CPP_O := $(addprefix HID__,$(notdir $(_HID_CPP:.cpp=.cpp.o)))

_OBJECTS = $(addprefix out/,main.cpp.o $(_AVR_S_O) $(_AVR_C_O) $(_AVR_CPP_O) $(_HID_CPP_O))

CFLAGS := \
    -flto \
    -O3 \
    -DF_CPU=$(_F_CPU) \
    -DUSB_VID=0x0f0d \
    -DUSB_PID=0x0092 \
    -DUSB_MANUFACTURER='"HORI CO.,LTD."' \
    -DUSB_PRODUCT='"POKKEN CONTROLLER"' \
    -DSPI_INTERFACES_COUNT=0 \
    -mmcu=$(_MCU) \
    -I$(_CORE) \
    -I$(AVRDIR)/variants/$(VARIANT) \
    -I$(_HID)


CXXFLAGS := \
    -std=c++11 \
    -fno-threadsafe-statics

.PHONY: all
all: main.hex

out:
	mkdir out

out/main.cpp.o: main.cpp | out
	avr-gcc -c $(CFLAGS) $(CXXFLAGS) -o $@ $<

out/HID__%.cpp.o: $(_HID)/%.cpp | out
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
