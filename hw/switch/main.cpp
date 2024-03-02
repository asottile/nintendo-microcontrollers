#include <Arduino.h>
#include <HID.h>

static const uint8_t _desc_data[] PROGMEM = {
    0x05, 0x01,
    0x09, 0x05,
    0xa1, 0x01,

    0x15, 0x00,
    0x25, 0x01,
    0x35, 0x00,
    0x45, 0x01,

    0x75, 0x01,
    0x95, 0x10,
    0x05, 0x09,
    0x19, 0x01,
    0x29, 0x10,

    0x81, 0x02,
    0x05, 0x01,
    0x25, 0x07, 0x46,
    0x3b, 0x01,
    0x75, 0x04,
    0x95, 0x01,
    0x65, 0x14,
    0x09, 0x39,

    0x81, 0x42,
    0x65, 0x00,
    0x95, 0x01,

    0x81, 0x01, 0x26,
    0xff, 0x00, 0x46,
    0xff, 0x00,
    0x09, 0x30,
    0x09, 0x31,
    0x09, 0x32,
    0x09, 0x35,
    0x75, 0x08,
    0x95, 0x04,

    0x81, 0x02, 0x06,
    0x00, 0xff,
    0x09, 0x20,
    0x95, 0x01,

    0x81, 0x02, 0x0a,
    0x21, 0x26,
    0x95, 0x08,
    0x91, 0x02,

    0xc0
};
static HIDSubDescriptor _desc{_desc_data, sizeof(_desc_data)};

class HIDWithoutReportID : public HID_ {
    public:
        int send_report(const void* data, size_t len) {
            // the switch does not use report ids
            return USB_Send(pluggedEndpoint | TRANSFER_RELEASE, data, len);
        }
};

typedef enum {
    BUTTON_Y       = 0x01,
    BUTTON_B       = 0x02,
    BUTTON_A       = 0x04,
    BUTTON_X       = 0x08,
    BUTTON_L       = 0x10,
    BUTTON_R       = 0x20,
    BUTTON_ZL      = 0x40,
    BUTTON_ZR      = 0x80,
    BUTTON_MINUS   = 0x100,
    BUTTON_PLUS    = 0x200,
    BUTTON_LCLICK  = 0x400,
    BUTTON_RCLICK  = 0x800,
    BUTTON_HOME    = 0x1000,
    BUTTON_CAPTURE = 0x2000,
} Buttons_t;

#define DPAD_TOP          0x00
#define DPAD_TOP_RIGHT    0x01
#define DPAD_RIGHT        0x02
#define DPAD_BOTTOM_RIGHT 0x03
#define DPAD_BOTTOM       0x04
#define DPAD_BOTTOM_LEFT  0x05
#define DPAD_LEFT         0x06
#define DPAD_TOP_LEFT     0x07
#define DPAD_CENTER       0x08

#define STICK_MIN      0
#define STICK_CENTER 128
#define STICK_MAX    255

typedef struct {
    uint16_t button;
    uint8_t dpad;
    uint8_t lx;
    uint8_t ly;
    uint8_t rx;
    uint8_t ry;
    uint8_t _unused;
} Report_t;

const int PIN_BUZZER = 9;

void make_report(Report_t* report, uint8_t c, uint8_t x, uint8_t y) {
    memset(report, 0, sizeof(Report_t));

    report->lx = report->ly = STICK_CENTER;
    report->rx = report->ry = STICK_CENTER;
    report->dpad = DPAD_CENTER;

    switch (c) {
        case 'A':
            report->button |= BUTTON_A;
            break;

        case 'B':
            report->button |= BUTTON_B;
            break;

        case 'X':
            report->button |= BUTTON_X;
            break;

        case 'Y':
            report->button |= BUTTON_Y;
            break;

        case 'H':
            report->button |= BUTTON_HOME;
            break;

        case '+':
            report->button |= BUTTON_PLUS;
            break;

        case '-':
            report->button |= BUTTON_MINUS;
            break;

        case 'L':
            report->button |= BUTTON_L;
            break;

        case 'R':
            report->button |= BUTTON_R;
            break;

        case 'l':
            report->button |= BUTTON_ZL;
            break;

        case 'r':
            report->button |= BUTTON_ZR;
            break;

        case 'w':
            report->ly = STICK_MIN;
            break;

        case 'a':
            report->lx = STICK_MIN;
            break;

        case 's':
            report->ly = STICK_MAX;
            break;

        case 'd':
            report->lx = STICK_MAX;
            break;

        case 'q':
            report->ly = STICK_MIN;
            report->lx = STICK_MIN;
            break;

        case 'e':
            report->ly = STICK_MIN;
            report->lx = STICK_MAX;
            break;

        case 'z':
            report->ly = STICK_MAX;
            report->lx = STICK_MIN;
            break;

        case 'c':
            report->ly = STICK_MAX;
            report->lx = STICK_MAX;
            break;

        case 'u':
            report->ry = STICK_MIN;
            break;

        case 'h':
            report->rx = STICK_MIN;
            break;

        case 'j':
            report->ry = STICK_MAX;
            break;

        case 'k':
            report->rx = STICK_MAX;
            break;

        case 'y':
            report->ry = STICK_MIN;
            report->rx = STICK_MIN;
            break;

        case 'i':
            report->ry = STICK_MIN;
            report->rx = STICK_MAX;
            break;

        case 'n':
            report->ry = STICK_MAX;
            report->rx = STICK_MIN;
            break;

        case 'm':
            report->ry = STICK_MAX;
            report->rx = STICK_MAX;
            break;

        case '~':
            report->button |= BUTTON_L | BUTTON_R;
            break;

        case '@':
            report->button |= BUTTON_A;
            report->ly = STICK_MAX;
            break;

        case '#':
            report->lx = STICK_MIN;
            report->rx = STICK_MIN;
            break;

        case '$':
            report->lx = (STICK_MAX - STICK_MIN) * 3 / 5;
            report->ly = (STICK_MAX - STICK_MIN) * 3 / 5;
            break;

        case '{':
            report->button = BUTTON_LCLICK;
            break;
        case '}':
            report->button = BUTTON_RCLICK;
            break;

        case '<':
            report->lx = x;
            report->ly = y;
            break;
        case '>':
            report->rx = x;
            report->ry = y;
            break;

        case 'C':
            report->button = BUTTON_CAPTURE;
            break;

        case '1':
            report->dpad = DPAD_RIGHT;
            break;
        case '2':
            report->dpad = DPAD_BOTTOM;
            break;
        case '3':
            report->dpad = DPAD_LEFT;
            break;
        case '4':
            report->dpad = DPAD_TOP;
            break;
    }
}

uint8_t serial_read_blocking() {
    while (!Serial1.available());
    return Serial1.read();
}

int main() {
    init();

    USBDevice.attach();

    HIDWithoutReportID hid;
    hid.AppendDescriptor(&_desc);

    Serial1.begin(9600);
    Serial1.println("hello hello world");

    pinMode(PIN_BUZZER, OUTPUT);

    Report_t report;
    bool verbose = false;
    uint8_t c = '.';
    uint8_t x = 0;
    uint8_t y = 0;
    while (true) {
        if (Serial1.available()) {
            char read = Serial1.read();
            if (read == 'V') {
                verbose = true;
                Serial1.println("enabling verbose mode");
            } else if (read == 'v') {
                verbose = false;
                Serial1.println("disabling verbose mode");
            } else if (read == '<' || read == '>') {
                c = read;
                x = serial_read_blocking();
                y = serial_read_blocking();
            } else {
                c = read;
                if (verbose) {
                    Serial1.print("recv: ");
                    Serial1.write(c);
                    Serial1.write('\n');
                }
            }

            digitalWrite(PIN_BUZZER, c == '!' ? HIGH : LOW);

            make_report(&report, c, x, y);
            hid.send_report(&report, sizeof(Report_t));
        }
    }
}
