#ifndef JSON_MESSENGER_H
#define JSON_MESSENGER_H

#include <Arduino.h>

// Struct to store incoming control commands from Control Station
struct TurretCommand {
    float pan = 0;
    float tilt = 0;
    bool laser1 = false;
    bool laser2 = false;
    bool laser3 = false;
    bool buzzer = false;
    String mode = "";
    bool valid = false; // Set true when a new command is received
};

// Struct to store incoming status messages from the Turret
struct TurretStatus {
    float pan_angle = 0;
    float tilt_angle = 0;
    float temp = 0;
    bool relay_laser1 = false;
    bool relay_servo1 = false;
    bool limit_left = false;
    bool limit_right = false;
    bool valid = false; // Set true when a new status message is received
};

class JsonMessenger {
public:
    void begin(HardwareSerial &serialPort, uint32_t baud, int rxPin, int txPin);

    // Send control commands (Control Station ➜ Turret)
    void sendCommand(float pan, float tilt, bool laser1, bool laser2, bool laser3, bool buzzer, const String &mode);

    // Send turret status feedback (Turret ➜ Control Station)
    void sendStatus(float pan_angle, float tilt_angle, float temp,
                    bool relay_laser1, bool relay_servo1,
                    bool limit_left, bool limit_right);

    // Call this regularly inside loop() to process incoming messages
    void update();

    // Exposed data structs
    TurretCommand lastCommand;
    TurretStatus lastStatus;

private:
    HardwareSerial* serial;
    String buffer;
    void processMessage(const String& jsonStr);
};

#endif
