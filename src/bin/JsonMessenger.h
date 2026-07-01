#ifndef JSON_MESSENGER_H
#define JSON_MESSENGER_H

#include <Arduino.h>
#include <ArduinoJson.h>

// ============= ControlCommand (Control ➜ Turret) ============
struct ControlCommand {
    bool system_enabled = false;

    struct {
        float pan_speed_rpm = 0.0f;
        float pan_min_angle = 0.0f;
        float pan_max_angle = 0.0f;
        float tilt_speed_rpm = 0.0f;
        float tilt_min_angle = 0.0f;
        float tilt_max_angle = 0.0f;
        float laser_focus_angle = 0.0f;
    } motion;

    struct {
        bool laser1_on = false;
        bool laser2_on = false;
        bool laser3_on = false;
        bool pan_motor_on = false;
        bool tilt_motor_on = false;
        bool buzzer_on = false;
    } actuator;

    bool valid = false;
};

// ============= TurretStatus (Turret ➜ Control) ============
struct TurretStatus {
    struct {
        float pan_angle_deg = 0.0f;
        float tilt_angle_deg = 0.0f;
        float pan_speed_rpm = 0.0f;
        float tilt_speed_rpm = 0.0f;
        float pan_voltage = 0.0f;
        float tilt_voltage = 0.0f;
    } motion;

    struct {
        bool laser_blue = false;
        bool laser_green = false;
        bool stage1 = false;
        bool stage2 = false;
        bool stage3 = false;
        bool manual_mode = false;
        bool confirm_target = false; // الجديد
    } buttons;

    struct {
        float pot_pan = 0.0f;
        float pot_tilt = 0.0f;
        float pot_focus = 0.0f;
        bool press = false;
    } joystick;

    bool valid = false;
};

// ===================== Messenger Class =====================
class JsonMessenger {
public:
    void begin(HardwareSerial &serialPort, uint32_t baud, int rxPin, int txPin);

    void sendCommand(const ControlCommand &cmd);
    void sendStatus(const TurretStatus &status);
    void receive();

    ControlCommand lastCommand;
    TurretStatus lastStatus;

private:
    HardwareSerial *serial;
    String buffer;
    void processMessage(const String &jsonStr);
};

#endif
