#include <Arduino.h>
#include <Wire.h>

const int PIN_A = 6;
const int PIN_B = 7;
const int PIN_X = 8;
const int PIN_Y = 9;
const int PIN_UP = 21;
const int PIN_LEFT = 20;
const int PIN_DOWN = 19;
const int PIN_RIGHT = 18;
const int PIN_L = 15;
const int PIN_R = 14;
const int PIN_START = 16;
const int PIN_SELECT = 10;
const int PIN_BUZZER = 5;
const int PIN_Y_READ = A6;

const float VCC = 4.59; // measured while plugged into usb
const float VMAX = 1.8;
const uint16_t SCALE = uint16_t(4095 * VMAX / VCC);
const uint16_t SCALE_Y = SCALE - 21;  // slightly innaccurate DACs?
const uint16_t SCALE_X = SCALE + 4;

const uint8_t DAC_Y = 0x62;
const uint8_t DAC_X = 0x63;

const uint8_t PARSE_POS = 1 << 7;
const uint8_t PARSE_X = 1 << 6;
const uint8_t PARSE_HIGH = 1 << 5;
const uint8_t PARSE_MASK = PARSE_HIGH - 1;

const uint16_t X_MAX = 319;
const uint16_t Y_MAX = 239;

void voltage(uint8_t addr, uint16_t f, bool store = false) {
    uint8_t data[3];
    data[0] = store ? 0x60 : 0x40;
    data[1] = f / 16;
    data[2] = (f % 16) << 4;
    Wire.beginTransmission(addr);
    Wire.write(data, 3);
    Wire.endTransmission();
}

int main() {
    init();

    USBDevice.attach();

    Serial.begin(9600);

    Wire.begin();
    Wire.setClock(400000);

    // atmega32u4 increase ADC speed
    ADCSRA = (ADCSRA & 0x80) | 0x04;

    voltage(DAC_Y, SCALE_Y, true);
    voltage(DAC_X, SCALE_X, true);

    pinMode(PIN_A, OUTPUT);
    pinMode(PIN_B, OUTPUT);
    pinMode(PIN_X, OUTPUT);
    pinMode(PIN_Y, OUTPUT);
    pinMode(PIN_UP, OUTPUT);
    pinMode(PIN_LEFT, OUTPUT);
    pinMode(PIN_DOWN, OUTPUT);
    pinMode(PIN_RIGHT, OUTPUT);
    pinMode(PIN_L, OUTPUT);
    pinMode(PIN_R, OUTPUT);
    pinMode(PIN_START, OUTPUT);
    pinMode(PIN_SELECT, OUTPUT);

    pinMode(PIN_BUZZER, OUTPUT);

    int c = '.';
    uint16_t x = 0;
    uint16_t y = 0;

    while (true) {
        if (Serial.available()) {
            c = Serial.read();
        }

        digitalWrite(PIN_A, c == 'A' ? LOW : HIGH);
        digitalWrite(PIN_B, c == 'B' ? LOW : HIGH);
        digitalWrite(PIN_X, c == 'X' ? LOW : HIGH);
        digitalWrite(PIN_Y, c == 'Y' ? LOW : HIGH);

        digitalWrite(PIN_UP, c == 'w' ? LOW : HIGH);
        digitalWrite(PIN_LEFT, c == 'a' ? LOW : HIGH);
        digitalWrite(PIN_DOWN, c == 's' ? LOW : HIGH);
        digitalWrite(PIN_RIGHT, c == 'd' ? LOW : HIGH);

        digitalWrite(PIN_L, (c == 'L' || c == '*') ? LOW : HIGH);
        digitalWrite(PIN_R, (c == 'R' || c == '*') ? LOW : HIGH);
        digitalWrite(PIN_START, (c == '[' || c == '*') ? LOW : HIGH);
        digitalWrite(PIN_SELECT, (c == ']' || c == '*') ? LOW : HIGH);

        digitalWrite(PIN_BUZZER, c == '!' ? HIGH : LOW);

        if (c & PARSE_POS) {
            uint16_t* target = (c & PARSE_X) ? &x : &y;
            uint8_t shift = (c & PARSE_HIGH) ? 5 : 0;

            *target &= ~(PARSE_MASK << shift);
            *target |= (c & PARSE_MASK) << shift;

            c = '.';
        } else if (c == 't') {
            uint16_t x_voltage = ((float)x / X_MAX) * SCALE_X;
            uint16_t y_voltage = ((float)y / Y_MAX) * SCALE_Y;

            voltage(DAC_X, x_voltage);
            voltage(DAC_Y, 0);

            uint32_t end = millis() + 300;
            while (millis() < end) {
                // wait until X is read (Y+ high)
                while (analogRead(PIN_Y_READ) < 300);
                // then delay until Y will be read
                delayMicroseconds(355);
                // write our Y value
                voltage(DAC_Y, y_voltage);
                delayMicroseconds(20);
                // continue touching
                voltage(DAC_Y, 0);
            }

            voltage(DAC_Y, SCALE_Y);
            voltage(DAC_X, 0);

            c = '.';
        }
    }
}
