#include <Arduino.h>

const int PIN_RESET = 2;

const int PIN_A = 3;
const int PIN_B = 4;
const int PIN_UP = 5;
const int PIN_LEFT = 6;
const int PIN_DOWN = 7;
const int PIN_RIGHT = 8;
const int PIN_START = 9;
const int PIN_SELECT = 14;
const int PIN_L = 16;
const int PIN_R = 10;

const int PIN_BUZZER = 1;

int main() {
    init();

    USBDevice.attach();

    Serial.begin(9600);

    pinMode(PIN_BUZZER, OUTPUT);

    int c = '.';

    while (true) {
        if (Serial.available()) {
            c = Serial.read();
        }

        pinMode(PIN_RESET, c == '*' ? OUTPUT : INPUT);

        pinMode(PIN_A, c == 'A' ? OUTPUT : INPUT);
        pinMode(PIN_B, (c == 'B' || c == '~') ? OUTPUT : INPUT);
        pinMode(PIN_UP, (c == 'w' || c == '~') ? OUTPUT : INPUT);
        pinMode(PIN_LEFT, c == 'a' ? OUTPUT : INPUT);
        pinMode(PIN_DOWN, c == 's' ? OUTPUT : INPUT);
        pinMode(PIN_RIGHT, c == 'd' ? OUTPUT : INPUT);
        pinMode(PIN_START, c == '[' ? OUTPUT : INPUT);
        pinMode(PIN_SELECT, (c == ']' || c == '~') ? OUTPUT : INPUT);
        pinMode(PIN_L, c == 'L' ? OUTPUT : INPUT);
        pinMode(PIN_R, c == 'R' ? OUTPUT : INPUT);

        digitalWrite(PIN_BUZZER, c == '!' ? HIGH : LOW);
    }
}
