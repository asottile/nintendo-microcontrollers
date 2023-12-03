#include "Joystick.h"
#include <LUFA/Drivers/Peripheral/Serial.h>

// Configures hardware and peripherals, such as the USB peripherals.
void SetupHardware(void) {
    // We need to disable watchdog if enabled by bootloader/fuses.
    MCUSR &= ~(1 << WDRF);
    wdt_disable();

    // We need to disable clock division before initializing the USB hardware.
    clock_prescale_set(clock_div_1);
    // We can then initialize our hardware and peripherals, including the USB stack.

    // enable pin 9 for output
    DDRB = 1 << 5;
    PORTB = 0;

    // The USB stack should be initialized last.
    Serial_Init(9600, 0);
    Serial_SendString("hello hello world\n");
    USB_Init();
}

// Fired when the host set the current configuration of the USB device after enumeration.
void EVENT_USB_Device_ConfigurationChanged(void) {
    Endpoint_ConfigureEndpoint(JOYSTICK_OUT_EPADDR, EP_TYPE_INTERRUPT, JOYSTICK_EPSIZE, 1);
    Endpoint_ConfigureEndpoint(JOYSTICK_IN_EPADDR, EP_TYPE_INTERRUPT, JOYSTICK_EPSIZE, 1);
}

void GetNextReport(USB_JoystickReport_Input_t* report, uint8_t c) {
    memset(report, 0, sizeof(USB_JoystickReport_Input_t));
    report->LX = STICK_CENTER;
    report->LY = STICK_CENTER;
    report->RX = STICK_CENTER;
    report->RY = STICK_CENTER;
    report->HAT = HAT_CENTER;

    switch (c) {
        case 'A':
            report->Button |= SWITCH_A;
            break;

        case 'B':
            report->Button |= SWITCH_B;
            break;

        case 'X':
            report->Button |= SWITCH_X;
            break;

        case 'Y':
            report->Button |= SWITCH_Y;
            break;

        case 'H':
            report->Button |= SWITCH_HOME;
            break;

        case '+':
            report->Button |= SWITCH_PLUS;
            break;

        case '-':
            report->Button |= SWITCH_MINUS;
            break;

        case 'L':
            report->Button |= SWITCH_L;
            break;

        case 'R':
            report->Button |= SWITCH_R;
            break;

        case 'l':
            report->Button |= SWITCH_ZL;
            break;

        case 'r':
            report->Button |= SWITCH_ZR;
            break;

        case 'w':
            report->LY = STICK_MIN;
            break;

        case 'a':
            report->LX = STICK_MIN;
            break;

        case 's':
            report->LY = STICK_MAX;
            break;

        case 'd':
            report->LX = STICK_MAX;
            break;

        case 'q':
            report->LY = STICK_MIN;
            report->LX = STICK_MIN;
            break;

        case 'e':
            report->LY = STICK_MIN;
            report->LX = STICK_MAX;
            break;

        case 'z':
            report->LY = STICK_MAX;
            report->LX = STICK_MIN;
            break;

        case 'c':
            report->LY = STICK_MAX;
            report->LX = STICK_MAX;
            break;

        case 'u':
            report->RY = STICK_MIN;
            break;

        case 'h':
            report->RX = STICK_MIN;
            break;

        case 'j':
            report->RY = STICK_MAX;
            break;

        case 'k':
            report->RX = STICK_MAX;
            break;

        case 'y':
            report->RY = STICK_MIN;
            report->RX = STICK_MIN;
            break;

        case 'i':
            report->RY = STICK_MIN;
            report->RX = STICK_MAX;
            break;

        case 'n':
            report->RY = STICK_MAX;
            report->RX = STICK_MIN;
            break;

        case 'm':
            report->RY = STICK_MAX;
            report->RX = STICK_MAX;
            break;

        case '~':
            report->Button |= SWITCH_L | SWITCH_R;
            break;

        case '@':
            report->Button |= SWITCH_A;
            report->LY = STICK_MAX;
            break;

        case '#':
            report->LX = STICK_MIN;
            report->RX = STICK_MIN;
            break;

        case '$':
            report->LX = (STICK_MAX - STICK_MIN) * 3 / 5;
            report->LY = (STICK_MAX - STICK_MIN) * 3 / 5;
            break;

        case '{':
            report->Button = SWITCH_LCLICK;
            break;
        case '}':
            report->Button = SWITCH_RCLICK;
            break;

        case '1':
            report->HAT = HAT_RIGHT;
            break;
        case '2':
            report->HAT = HAT_BOTTOM;
            break;
        case '3':
            report->HAT = HAT_LEFT;
            break;
        case '4':
            report->HAT = HAT_TOP;
            break;
    }
}

void HID_Task(uint8_t c) {
    if (USB_DeviceState != DEVICE_STATE_Configured)
        return;

    Endpoint_SelectEndpoint(JOYSTICK_OUT_EPADDR);
    if (Endpoint_IsOUTReceived()) {
        if (Endpoint_IsReadWriteAllowed()) {
            USB_JoystickReport_Output_t JoystickOutputData;
            while(Endpoint_Read_Stream_LE(&JoystickOutputData, sizeof(JoystickOutputData), NULL) != ENDPOINT_RWSTREAM_NoError);
        }
        Endpoint_ClearOUT();
    }

    Endpoint_SelectEndpoint(JOYSTICK_IN_EPADDR);
    if (Endpoint_IsINReady()) {
        USB_JoystickReport_Input_t JoystickInputData;
        GetNextReport(&JoystickInputData, c);
        while(Endpoint_Write_Stream_LE(&JoystickInputData, sizeof(JoystickInputData), NULL) != ENDPOINT_RWSTREAM_NoError);
        Endpoint_ClearIN();
    }
}

int main(void) {
    SetupHardware();
    GlobalInterruptEnable();

    // listen for inputs and react
    bool verbose = false;
    char c = '0';
    for (;;) {
        if (Serial_IsCharReceived()) {
            char read = Serial_ReceiveByte();
            if (read == 'V') {
                verbose = true;
                Serial_SendString("enabling verbose mode\n");
            } else if (read == 'v') {
                verbose = false;
                Serial_SendString("disabling verbose mode\n");
            } else {
                c = read;
                if (verbose) {
                    Serial_SendString("recv: ");
                    Serial_SendByte(c);
                    Serial_SendByte('\n');
                }
            }
        }

        PORTB = c == '!' ? (1 << 5) : 0;

        HID_Task(c);
        USB_USBTask();
    }
}
