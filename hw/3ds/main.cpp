#include <Arduino.h>

static const int PIN_MIN = 2;
static const int PIN_BUZZER = 10;

int main() {
    init();

    USBDevice.attach();

    Serial.begin(9600);

    for (int pin = PIN_MIN; pin <= PIN_BUZZER; pin += 1) {
        pinMode(pin, OUTPUT);
    }

    int c = '.';

    while (true) {
        if (Serial.available()) {
            c = Serial.read();
        }

        digitalWrite(PIN_MIN + 0, c == 'A' ? LOW : HIGH);
        digitalWrite(PIN_MIN + 1, c == 'B' ? LOW : HIGH);
        digitalWrite(PIN_MIN + 2, c == 'X' ? LOW : HIGH);
        digitalWrite(PIN_MIN + 3, c == 'Y' ? LOW : HIGH);
        digitalWrite(PIN_MIN + 4, c == 'w' ? LOW : HIGH);
        digitalWrite(PIN_MIN + 5, c == 'a' ? LOW : HIGH);
        digitalWrite(PIN_MIN + 6, c == 's' ? LOW : HIGH);
        digitalWrite(PIN_MIN + 7, c == 'd' ? LOW : HIGH);
        digitalWrite(PIN_BUZZER, c == '!' ? HIGH : LOW);
    }
}
