#include <Arduino.h>
#include <Wire.h>

const int PIN_A = 9;
const int PIN_B = 6;
const int PIN_X = 5;
const int PIN_Y = 7;
const int PIN_R = 8;
const int PIN_HOME = 4;

const int PIN_BUZZER = 16;

const float VCC = 4.59; // measured while plugged into usb
const float VMAX = 1.8;
const uint16_t SCALE = uint16_t(4095 * VMAX / VCC);

const uint16_t Y_MAX = SCALE + 4;  // slightly innaccurate DACs?
const uint16_t Y_MID = Y_MAX * .8 / 1.8;
const uint16_t Y_MIN = 0;

const uint16_t X_MAX = SCALE + 12;
const uint16_t X_MID = X_MAX * .8 / 1.8;
const uint16_t X_MIN = 0;

const uint8_t DAC_Y = 0x62;
const uint8_t DAC_X = 0x63;

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

    voltage(DAC_Y, Y_MID, true);
    voltage(DAC_X, X_MID, true);

    pinMode(PIN_A, OUTPUT);
    pinMode(PIN_B, OUTPUT);
    pinMode(PIN_X, OUTPUT);
    pinMode(PIN_Y, OUTPUT);
    pinMode(PIN_R, OUTPUT);
    pinMode(PIN_HOME, OUTPUT);

    pinMode(PIN_BUZZER, OUTPUT);

    int c = '.';
    uint16_t current_x = X_MID;
    uint16_t current_y = Y_MID;
    while (true) {
        if (Serial.available()) {
            c = Serial.read();
        }

        digitalWrite(PIN_A, c == 'A' ? HIGH : LOW);
        digitalWrite(PIN_B, c == 'B' ? HIGH : LOW);
        digitalWrite(PIN_X, c == 'X' ? HIGH : LOW);
        digitalWrite(PIN_Y, c == 'Y' ? HIGH : LOW);
        digitalWrite(PIN_R, c == 'R' ? HIGH : LOW);
        digitalWrite(PIN_HOME, c == 'H' ? HIGH : LOW);

        digitalWrite(PIN_BUZZER, c == '!' ? HIGH : LOW);

        uint16_t vx = X_MID;
        uint16_t vy = Y_MID;
        switch (c) {
            case 'w':
                vy = Y_MAX;
                break;
            case 'a':
                vx = X_MAX;
                break;
            case 's':
                vy = Y_MIN;
                break;
            case 'd':
                vx = X_MIN;
                break;
        }
        voltage(DAC_X, vx);
        voltage(DAC_Y, vy);
    }
}
