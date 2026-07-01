#include "JsonMessenger.h"
#include <ArduinoJson.h>

#define DEBUG_SERIAL Serial

void JsonMessenger::begin(HardwareSerial &serialPort, uint32_t baud, int rxPin, int txPin) {
    serial = &serialPort;
    serial->begin(baud, SERIAL_8N1, rxPin, txPin);
    buffer.reserve(256);
}

void JsonMessenger::sendCommand(float pan, float tilt, bool laser1, bool laser2, bool laser3, bool buzzer, const String &mode) {
    StaticJsonDocument<200> doc;

    doc["type"] = "command";
    doc["pan"] = pan;
    doc["tilt"] = tilt;
    doc["laser1"] = laser1;
    doc["laser2"] = laser2;
    doc["laser3"] = laser3;
    doc["buzzer"] = buzzer;
    doc["mode"] = mode;

    serializeJson(doc, *serial);
    serial->println();
}

void JsonMessenger::sendStatus(float pan_angle, float tilt_angle, float temp,
                               bool relay_laser1, bool relay_servo1,
                               bool limit_left, bool limit_right) {
    StaticJsonDocument<200> doc;

    doc["type"] = "status";
    doc["pan_angle"] = pan_angle;
    doc["tilt_angle"] = tilt_angle;
    doc["temp"] = temp;

    JsonObject relay = doc.createNestedObject("relay");
    relay["laser1"] = relay_laser1;
    relay["servo1"] = relay_servo1;

    JsonObject limit = doc.createNestedObject("limit");
    limit["pan_left"] = limit_left;
    limit["pan_right"] = limit_right;

    serializeJson(doc, *serial);
    serial->println();
}

void JsonMessenger::update() {
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

void JsonMessenger::processMessage(const String &jsonStr) {
    StaticJsonDocument<256> doc;
    DeserializationError error = deserializeJson(doc, jsonStr);

    if (!error) {
        const char* type = doc["type"];
        
        if (strcmp(type, "command") == 0) {
            lastCommand.pan = doc["pan"] | 0.0;
            lastCommand.tilt = doc["tilt"] | 0.0;
            lastCommand.laser1 = doc["laser1"] | false;
            lastCommand.laser2 = doc["laser2"] | false;
            lastCommand.laser3 = doc["laser3"] | false;
            lastCommand.buzzer = doc["buzzer"] | false;
            lastCommand.mode = doc["mode"].isNull() ? "" : String(doc["mode"].as<const char*>());
            lastCommand.valid = true;

            DEBUG_SERIAL.println("✅ Received and parsed command.");

        } else if (strcmp(type, "status") == 0) {
            lastStatus.pan_angle = doc["pan_angle"] | 0.0;
            lastStatus.tilt_angle = doc["tilt_angle"] | 0.0;
            lastStatus.temp = doc["temp"] | 0.0;
            lastStatus.relay_laser1 = doc["relay"]["laser1"] | false;
            lastStatus.relay_servo1 = doc["relay"]["servo1"] | false;
            lastStatus.limit_left = doc["limit"]["pan_left"] | false;
            lastStatus.limit_right = doc["limit"]["pan_right"] | false;
            lastStatus.valid = true;

            DEBUG_SERIAL.println("✅ Received and parsed status.");

        } else {
            DEBUG_SERIAL.println("⚠️ Unknown message type received.");
        }

    } else {
        DEBUG_SERIAL.print("❌ JSON Parse Error: ");
        DEBUG_SERIAL.println(error.c_str());
    }
}
