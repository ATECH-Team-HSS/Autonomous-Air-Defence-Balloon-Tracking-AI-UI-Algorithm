#include "JsonMessenger.h"
#include <ArduinoJson.h>

#define DEBUG_SERIAL Serial

void JsonMessenger::begin(HardwareSerial &serialPort, uint32_t baud, int rxPin, int txPin) {
    serial = &serialPort;
    serial->begin(baud, SERIAL_8N1, rxPin, txPin);
    buffer.reserve(512);
}

// =============== Send Command ===============
void JsonMessenger::sendCommand(const ControlCommand &cmd) {
    StaticJsonDocument<384> doc;
    doc["type"] = "command";
    doc["system_enabled"] = cmd.system_enabled;

    JsonObject motion = doc.createNestedObject("motion");
    motion["pan_speed_rpm"] = cmd.motion.pan_speed_rpm;
    motion["pan_min_angle"] = cmd.motion.pan_min_angle;
    motion["pan_max_angle"] = cmd.motion.pan_max_angle;
    motion["tilt_speed_rpm"] = cmd.motion.tilt_speed_rpm;
    motion["tilt_min_angle"] = cmd.motion.tilt_min_angle;
    motion["tilt_max_angle"] = cmd.motion.tilt_max_angle;
    motion["laser_focus_angle"] = cmd.motion.laser_focus_angle;

    JsonObject act = doc.createNestedObject("actuator");
    act["laser1_on"] = cmd.actuator.laser1_on;
    act["laser2_on"] = cmd.actuator.laser2_on;
    act["laser3_on"] = cmd.actuator.laser3_on;
    act["pan_motor_on"] = cmd.actuator.pan_motor_on;
    act["tilt_motor_on"] = cmd.actuator.tilt_motor_on;
    act["buzzer_on"] = cmd.actuator.buzzer_on;

    serializeJson(doc, *serial);
    serial->println();
}

// =============== Send Status ===============
void JsonMessenger::sendStatus(const TurretStatus &status) {
    StaticJsonDocument<384> doc;
    doc["type"] = "status";

    JsonObject motion = doc.createNestedObject("motion");
    motion["pan_angle_deg"] = status.motion.pan_angle_deg;
    motion["tilt_angle_deg"] = status.motion.tilt_angle_deg;
    motion["pan_speed_rpm"] = status.motion.pan_speed_rpm;
    motion["tilt_speed_rpm"] = status.motion.tilt_speed_rpm;
    motion["pan_voltage"] = status.motion.pan_voltage;
    motion["tilt_voltage"] = status.motion.tilt_voltage;

    JsonObject btn = doc.createNestedObject("buttons");
    btn["laser_blue"] = status.buttons.laser_blue;
    btn["laser_green"] = status.buttons.laser_green;
    btn["stage1"] = status.buttons.stage1;
    btn["stage2"] = status.buttons.stage2;
    btn["stage3"] = status.buttons.stage3;
    btn["manual_mode"] = status.buttons.manual_mode;
    btn["confirm_target"] = status.buttons.confirm_target;

    JsonObject joy = doc.createNestedObject("joystick");
    joy["pot_pan"] = status.joystick.pot_pan;
    joy["pot_tilt"] = status.joystick.pot_tilt;
    joy["pot_focus"] = status.joystick.pot_focus;
    joy["press"] = status.joystick.press;

    serializeJson(doc, *serial);
    serial->println();
}

// =============== Receive and Parse ===============
void JsonMessenger::receive() {
    while (serial->available()) {
        char c = (char)serial->read();
        if (c == '\n') {
            processMessage(buffer);
            buffer = "";
        } else {
            buffer += c;
        }
    }
}

// =============== Process JSON ===============
void JsonMessenger::processMessage(const String &jsonStr) {
    StaticJsonDocument<512> doc;
    DeserializationError err = deserializeJson(doc, jsonStr);

    if (err) {
        DEBUG_SERIAL.print(F("❌ JSON parse error: "));
        DEBUG_SERIAL.println(err.c_str());
        return;
    }

    const char* type = doc["type"];
    if (!type) {
        DEBUG_SERIAL.println(F("⚠️ Missing type"));
        return;
    }

    if (strcmp(type, "command") == 0) {
        lastCommand.system_enabled = doc["system_enabled"] | false;

        JsonObject motion = doc["motion"];
        lastCommand.motion.pan_speed_rpm = motion["pan_speed_rpm"] | 0.0f;
        lastCommand.motion.pan_min_angle = motion["pan_min_angle"] | 0.0f;
        lastCommand.motion.pan_max_angle = motion["pan_max_angle"] | 0.0f;
        lastCommand.motion.tilt_speed_rpm = motion["tilt_speed_rpm"] | 0.0f;
        lastCommand.motion.tilt_min_angle = motion["tilt_min_angle"] | 0.0f;
        lastCommand.motion.tilt_max_angle = motion["tilt_max_angle"] | 0.0f;
        lastCommand.motion.laser_focus_angle = motion["laser_focus_angle"] | 0.0f;

        JsonObject act = doc["actuator"];
        lastCommand.actuator.laser1_on = act["laser1_on"] | false;
        lastCommand.actuator.laser2_on = act["laser2_on"] | false;
        lastCommand.actuator.laser3_on = act["laser3_on"] | false;
        lastCommand.actuator.pan_motor_on = act["pan_motor_on"] | false;
        lastCommand.actuator.tilt_motor_on = act["tilt_motor_on"] | false;
        lastCommand.actuator.buzzer_on = act["buzzer_on"] | false;

        lastCommand.valid = true;
        DEBUG_SERIAL.println(F("✅ Command parsed"));

    } else if (strcmp(type, "status") == 0) {
        JsonObject motion = doc["motion"];
        lastStatus.motion.pan_angle_deg = motion["pan_angle_deg"] | 0.0f;
        lastStatus.motion.tilt_angle_deg = motion["tilt_angle_deg"] | 0.0f;
        lastStatus.motion.pan_speed_rpm = motion["pan_speed_rpm"] | 0.0f;
        lastStatus.motion.tilt_speed_rpm = motion["tilt_speed_rpm"] | 0.0f;
        lastStatus.motion.pan_voltage = motion["pan_voltage"] | 0.0f;
        lastStatus.motion.tilt_voltage = motion["tilt_voltage"] | 0.0f;

        JsonObject btn = doc["buttons"];
        lastStatus.buttons.laser_blue = btn["laser_blue"] | false;
        lastStatus.buttons.laser_green = btn["laser_green"] | false;
        lastStatus.buttons.stage1 = btn["stage1"] | false;
        lastStatus.buttons.stage2 = btn["stage2"] | false;
        lastStatus.buttons.stage3 = btn["stage3"] | false;
        lastStatus.buttons.manual_mode = btn["manual_mode"] | false;
        lastStatus.buttons.confirm_target = btn["confirm_target"] | false;

        JsonObject joy = doc["joystick"];
        lastStatus.joystick.pot_pan = joy["pot_pan"] | 0.0f;
        lastStatus.joystick.pot_tilt = joy["pot_tilt"] | 0.0f;
        lastStatus.joystick.pot_focus = joy["pot_focus"] | 0.0f;
        lastStatus.joystick.press = joy["press"] | false;

        lastStatus.valid = true;
        DEBUG_SERIAL.println(F("✅ Status parsed"));
    } else {
        DEBUG_SERIAL.print(F("⚠️ Unknown type: "));
        DEBUG_SERIAL.println(type);
    }
}
