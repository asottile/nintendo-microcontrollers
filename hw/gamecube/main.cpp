#include <Arduino.h>
#include <Nintendo.h>

const int PIN_RESET = 8;
const int PIN_BUZZER = 9;
const int PIN_GC = 10;

int main() {
    init();

    USBDevice.attach();

    Serial.begin(9600);

    pinMode(PIN_RESET, INPUT);

    pinMode(PIN_GC, OUTPUT);
    CGamecubeConsole console(PIN_GC);

    pinMode(PIN_BUZZER, OUTPUT);

    int c = '.';
    Gamecube_Data_t data = defaultGamecubeData;

    while (true) {
        if (Serial.available()) {
            c = Serial.read();
        }

        if (c == '*') {
            pinMode(PIN_RESET, OUTPUT);
            digitalWrite(PIN_RESET, LOW);
        } else {
            pinMode(PIN_RESET, INPUT);
        }
        digitalWrite(PIN_BUZZER, c == '!' ? HIGH : LOW);

        data.report.a = (c == 'A');
        data.report.b = (c == 'B');
        data.report.x = (c == 'X');
        data.report.y = (c == 'Y');
        data.report.z = (c == 'Z');
        data.report.start = (c == '[');
        data.report.r = (c == 'R');
        data.report.l = (c == 'L');
        data.report.dup = (c == 'w' || c == 'q' || c == 'e');
        data.report.dleft = (c == 'a' || c == 'q' || c == 'z');
        data.report.ddown = (c == 's' || c == 'z' || c == 'c');
        data.report.dright = (c == 'd' || c == 'e' || c == 'c');

        console.write(data);
    }
}
