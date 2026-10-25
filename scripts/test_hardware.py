import serial
import time
import glob

def find_serial_port():
    ports = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
    if ports:
        return ports[0]
    return None

def test_fsm():
    port = find_serial_port()
    if not port:
        print("FAIL: No serial port found.")
        return

    try:
        # Connect to the hardware
        ser = serial.Serial(port, 115200, timeout=1)
        print(f"Connected to {port}.")
    except Exception as e:
        print(f"FAIL: Could not open {port} - {e}")
        return

    # Wait a moment for connection to stabilize
    time.sleep(2)
    ser.reset_input_buffer()

    print("\n--- AUTOMATED HARDWARE-IN-THE-LOOP TEST ---")
    print("Sending simulated CV Target P:50.0% to trigger the FSM sequence...")
    ser.write(b"P:50.0\n")

    expected_states = ["ACQUIRE", "FORWARD", "CLEAN", "DOCK"]
    current_idx = 0
    start_time = time.time()
    
    print("Awaiting telemetry and state transitions...")

    while time.time() - start_time < 15: # Timeout after 15s
        if ser.in_waiting:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line:
                print(f"ESP32_RX: {line}")
                if line.startswith("[STATE]"):
                    state = line.split(" ")[1]
                    if current_idx < len(expected_states) and state == expected_states[current_idx]:
                        print(f">>> VERIFIED TRANSITION TO: {state}")
                        current_idx += 1
                        
                        if current_idx == len(expected_states):
                            print("\n==================================================")
                            print("✅ SUCCESS: ALL FSM STATES EXECUTED FLAWLESSLY!")
                            print("The microcontroller successfully advanced through ACQUIRE -> FORWARD -> CLEAN -> DOCK.")
                            print("At this point, the ESP32 is actively holding the DOCK state (IN2 reverse) until the physical limit switch is depressed.")
                            print("==================================================")
                            ser.close()
                            return
    
    print("\n❌ FAIL: Did not reach all expected states within the 15-second timeout.")
    ser.close()

if __name__ == "__main__":
    test_fsm()
