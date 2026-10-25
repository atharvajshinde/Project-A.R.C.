#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_INA219.h>

// -------------------------------------------------------------------------
// SECTION 8 & PROMPT PIN MAPPING (v2.0)
// -------------------------------------------------------------------------
const int PIN_LIMIT = 33; 
const int PIN_RELAY = 32; 

// N20 Traversal Drive Motors (L298N Channel A)
const int PIN_ENA = 25;
const int PIN_IN1 = 26;
const int PIN_IN2 = 27;

// 25GA Roller Brush Motor (L298N Channel B)
const int PIN_IN3 = 14;
const int PIN_IN4 = 12;
const int PIN_ENB = 13;

// -------------------------------------------------------------------------
// SECTION 6: FINITE STATE MACHINE (FSM) DEFINITIONS
// -------------------------------------------------------------------------
enum SystemState {
    STATE_IDLE = 0,
    STATE_ACQUIRE = 1,
    STATE_FORWARD = 2,
    STATE_CLEAN = 3,
    STATE_DOCK = 4
};

volatile SystemState currentState = STATE_IDLE;
SystemState lastState = STATE_DOCK; // Forcing an initial state print

float pTarget = 0.0;
unsigned long stateStartTime = 0;
unsigned long tRun = 0; 

// -------------------------------------------------------------------------
// TELEMETRY GLOBALS (Section 6.2 & Prompt)
// -------------------------------------------------------------------------
Adafruit_INA219 ina219;
bool ina219_connected = false;

float busVoltage = 0.0;
float current_mA = 0.0;
float power_mW = 0.0;
float pDirty = 0.0;
float pClean = 0.0;
float etaGain = 0.0;

unsigned long lastTelemetryTime = 0;

// -------------------------------------------------------------------------
// ACTUATOR CONTROL HELPERS
// -------------------------------------------------------------------------
void stopAllActuators() {
    digitalWrite(PIN_IN1, LOW);
    digitalWrite(PIN_IN2, LOW);
    digitalWrite(PIN_IN3, LOW);
    digitalWrite(PIN_IN4, LOW);
    digitalWrite(PIN_RELAY, LOW);
    analogWrite(PIN_ENA, 0);
    analogWrite(PIN_ENB, 0);
}

void rampMotor(int enablePin, int startPwm, int endPwm, int durationMs) {
    const int steps = 15;
    int stepTime = durationMs / steps;
    for (int i = 0; i <= steps; i++) {
        int pwm = startPwm + (endPwm - startPwm) * i / steps;
        analogWrite(enablePin, pwm);
        delay(stepTime);
    }
}

// -------------------------------------------------------------------------
// INTERRUPT SERVICE ROUTINE (ISR)
// -------------------------------------------------------------------------
void IRAM_ATTR limitSwitchISR() {
    digitalWrite(PIN_IN1, LOW);
    digitalWrite(PIN_IN2, LOW);
    digitalWrite(PIN_IN3, LOW);
    digitalWrite(PIN_IN4, LOW);
    digitalWrite(PIN_RELAY, LOW);
    analogWrite(PIN_ENA, 0);
    analogWrite(PIN_ENB, 0);
    currentState = STATE_IDLE;
}

const char* getStateName(SystemState s) {
    switch(s) {
        case STATE_IDLE: return "IDLE";
        case STATE_ACQUIRE: return "ACQUIRE";
        case STATE_FORWARD: return "FORWARD";
        case STATE_CLEAN: return "CLEAN";
        case STATE_DOCK: return "DOCK";
        default: return "UNKNOWN";
    }
}

void setup() {
    Serial.begin(115200);

    // Initialize I2C (Pins 21 SDA, 22 SCL @ 100 kHz) with timeout protection
    Wire.begin(21, 22);
    Wire.setClock(100000);
    Wire.setTimeOut(25); // Prevent I2C bus hang from motor EMF transients

    if (!ina219.begin()) {
        Serial.println("Warning: INA219 not found! Auto-fallback to mock telemetry enabled.");
        ina219_connected = false;
    } else {
        ina219_connected = true;
    }

    pinMode(PIN_LIMIT, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(PIN_LIMIT), limitSwitchISR, FALLING);

    pinMode(PIN_RELAY, OUTPUT);
    digitalWrite(PIN_RELAY, LOW); 

    // Drive Motors (Channel A)
    pinMode(PIN_ENA, OUTPUT);
    pinMode(PIN_IN1, OUTPUT);
    pinMode(PIN_IN2, OUTPUT);
    analogWrite(PIN_ENA, 0);
    digitalWrite(PIN_IN1, LOW);
    digitalWrite(PIN_IN2, LOW);

    // Brush Motor (Channel B)
    pinMode(PIN_ENB, OUTPUT);
    pinMode(PIN_IN3, OUTPUT);
    pinMode(PIN_IN4, OUTPUT);
    analogWrite(PIN_ENB, 0);
    digitalWrite(PIN_IN3, LOW);
    digitalWrite(PIN_IN4, LOW);
}

void sampleTelemetry() {
    if (ina219_connected) {
        busVoltage = ina219.getBusVoltage_V();
        current_mA = ina219.getCurrent_mA();
        power_mW = ina219.getPower_mW();
    } else {
        // Mock telemetry behavior for desk testing when sensor is unwired
        busVoltage = 7.4 + ((random(0, 20) - 10) / 100.0);
        
        // Simulate load based on state
        if (currentState == STATE_FORWARD || currentState == STATE_DOCK) {
            current_mA = 240.0 + random(0, 30);
        } else if (currentState == STATE_CLEAN) {
            current_mA = 680.0 + random(0, 50); // Brush + blower load
        } else {
            current_mA = 25.0 + random(0, 10);
        }
        
        power_mW = busVoltage * current_mA;
    }
}

void loop() {
    // 1. Emit State Changes (only on change)
    if (currentState != lastState) {
        Serial.print("[STATE] ");
        Serial.println(getStateName(currentState));
        lastState = currentState;
    }

    // 2. Transmit Structured Telemetry (10 Hz)
    if (millis() - lastTelemetryTime >= 100) {
        sampleTelemetry();
        // Format: DATA,state,voltage_v,current_ma,power_mw,gain_pct
        Serial.printf("DATA,%d,%.2f,%.2f,%.2f,%.2f\n", 
                      currentState, busVoltage, current_mA, power_mW, etaGain);
        lastTelemetryTime = millis();
    }

    // 3. Non-Blocking FSM Core
    switch (currentState) {
        
        case STATE_IDLE: {
            stopAllActuators();

            if (Serial.available() > 0) {
                String msg = Serial.readStringUntil('\n');
                if (msg.startsWith("P:")) {
                    pTarget = msg.substring(2).toFloat();
                    currentState = STATE_ACQUIRE;
                }
            }
            break;
        }
        
        case STATE_ACQUIRE: {
            // Eq. 21 transit approximation based on P_target mapping
            tRun = (unsigned long)((pTarget / 100.0) * 2650.0);
            
            // Staggered soft-start for FORWARD locomotion
            digitalWrite(PIN_IN1, HIGH);
            digitalWrite(PIN_IN2, LOW);
            rampMotor(PIN_ENA, 80, 255, 300);

            currentState = STATE_FORWARD;
            stateStartTime = millis();
            break;
        }
        
        case STATE_FORWARD: {
            if (millis() - stateStartTime >= tRun) {
                // Cut locomotion drive
                digitalWrite(PIN_IN1, LOW);
                digitalWrite(PIN_IN2, LOW);
                analogWrite(PIN_ENA, 0);
                
                // Sample Baseline Power (P_dirty) right before cleaning
                sampleTelemetry();
                pDirty = power_mW;

                // Staggered cleaning startup:
                // 1. Start 25GA brush motor first with 300 ms PWM ramp (80 -> 255)
                digitalWrite(PIN_IN3, HIGH);
                digitalWrite(PIN_IN4, LOW);
                rampMotor(PIN_ENB, 80, 255, 300);

                // 2. Wait 200 ms for inrush current to settle
                delay(200);

                // 3. Engage 5015 blower fan via relay
                digitalWrite(PIN_RELAY, HIGH);

                currentState = STATE_CLEAN;
                stateStartTime = millis();
            }
            break;
        }
        
        case STATE_CLEAN: {
            if (millis() - stateStartTime >= 3000) { 
                // Sample Final Power (P_clean) and compute gain (Eq. 16)
                sampleTelemetry();
                pClean = power_mW;
                
                if (pDirty > 0) {
                    etaGain = ((pClean - pDirty) / pDirty) * 100.0;
                }
                
                // Shut down cleaning actuators
                digitalWrite(PIN_RELAY, LOW); 
                digitalWrite(PIN_IN3, LOW);
                digitalWrite(PIN_IN4, LOW);
                analogWrite(PIN_ENB, 0);

                // Start reverse traversal towards docking limit switch
                digitalWrite(PIN_IN1, LOW);
                digitalWrite(PIN_IN2, HIGH);
                rampMotor(PIN_ENA, 80, 255, 300);

                currentState = STATE_DOCK;
                stateStartTime = millis();
            }
            break;
        }
        
        case STATE_DOCK: {
            // Safety Watchdog: If limit switch fails to trip within (tRun + 3000 ms),
            // cut all motors and return to IDLE to prevent stalling/burnout.
            if (millis() - stateStartTime >= (tRun + 3000)) {
                stopAllActuators();
                currentState = STATE_IDLE;
                Serial.println("[WATCHDOG] DOCK timeout expired: limit switch failed to trip, stopping motors.");
            }
            // Limit switch ISR handles normal return to IDLE
            break;
        }
    }
}
