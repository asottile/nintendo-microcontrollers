#include <Arduino.h>

static const int BUZZER = 10;

int main() {
    init();

    USBDevice.attach();

    Serial.begin(9600);

    pinMode(BUZZER, OUTPUT);

    int c = '.';

    while (true) {
        if (Serial.available()) {
            c = Serial.read();
        }

        digitalWrite(BUZZER, c == '!' ? HIGH : LOW);
    }
}
