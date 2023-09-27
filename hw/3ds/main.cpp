#include <Arduino.h>

const int PIN_A = 2;
const int PIN_B = 3;
const int PIN_X = 4;
const int PIN_Y = 5;
const int PIN_UP = 6;
const int PIN_LEFT = 7;
const int PIN_DOWN = 8;
const int PIN_RIGHT = 9;
const int PIN_L = 15;
const int PIN_R = 14;
const int PIN_START = 16;
const int PIN_SELECT = 10;
const int PIN_BUZZER = 18;

int main() {
    init();

    USBDevice.attach();

    Serial.begin(9600);

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

        bool L_pressed = false;
        bool R_pressed = false;
        bool start_pressed = false;
        bool select_pressed = false;

        switch (c) {
            case 'L':
                L_pressed = true;
                break;
            case 'R':
                R_pressed = true;
                break;
            case '[':
                start_pressed = true;
                break;
            case ']':
                select_pressed = true;
                break;
            case '*':
                L_pressed = R_pressed = start_pressed = select_pressed = true;
                break;
        }

        digitalWrite(PIN_L, L_pressed ? LOW : HIGH);
        digitalWrite(PIN_R, R_pressed ? LOW : HIGH);
        digitalWrite(PIN_START, start_pressed ? LOW : HIGH);
        digitalWrite(PIN_SELECT, select_pressed ? LOW : HIGH);

        digitalWrite(PIN_BUZZER, c == '!' ? HIGH : LOW);
    }
}
