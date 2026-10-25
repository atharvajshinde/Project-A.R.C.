import os
# Must be set before cv2 loads its bundled Qt: use X11 and silence font/plugin spam.
os.environ.setdefault("QT_QPA_PLATFORM", "xcb")
os.environ.setdefault("QT_LOGGING_RULES", "*=false")

import cv2
import numpy as np
import serial
import time
import glob
import threading
import csv
import logging
import sys
import traceback
from collections import deque

from arc_gui import Dashboard

# -----------------------------------------------------------------------------
# DETAILED DIAGNOSTIC LOGGING SYSTEM SETUP
# -----------------------------------------------------------------------------
# We create a logger that outputs simplified info to the terminal, but records
# extremely detailed debug traces (with timestamps and thread names) to a file.
logger = logging.getLogger("ARC_Vision")
logger.setLevel(logging.DEBUG)

# File Handler (Highly Detailed: Captures all DEBUG traces and exceptions)
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
fh = logging.FileHandler(os.path.join(LOG_DIR, 'vision_pipeline_debug.log'))
fh.setLevel(logging.DEBUG)

# Console Handler (Standard Info: Keeps terminal uncluttered but informative)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)

# Formatter (Format: Time - Level - Thread - Function:Line - Message)
formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(threadName)s - %(funcName)s:%(lineno)d - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(ch)
# -----------------------------------------------------------------------------


# Shared state for background telemetry
telemetry_data = {
    'state': 'IDLE',
    'state_id': 0,
    'voltage_v': 0.0,
    'current_ma': 0.0,
    'power_mw': 0.0,
    'gain_pct': 0.0,
    'p_target': 0.0,
    't_run': 0.0
}

def find_serial_port():
    logger.debug("Probing for ESP32 serial ports...")
    ports = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
    if ports:
        logger.info(f"Found serial ports: {ports}")
        return ports[0]
    logger.warning("No ESP32 serial ports found during probe.")
    return None

def serial_listener(ser, csv_writer, log_file):
    logger.info("Serial listener thread started.")
    while True:
        try:
            if ser.in_waiting:
                raw_line = ser.readline()
                line = raw_line.decode('utf-8', errors='replace').strip()
                if not line:
                    continue
                
                # Log all incoming packets to the debug file
                logger.debug(f"SERIAL RX: {line}")
                
                if line.startswith('[STATE]'):
                    state_name = line.split(' ', 1)[1]
                    telemetry_data['state'] = state_name
                    logger.info(f"ESP32 FSM Transition -> {state_name}")
                
                elif line.startswith('DATA,'):
                    parts = line.split(',')
                    if len(parts) == 6:
                        telemetry_data['state_id'] = int(parts[1])
                        telemetry_data['voltage_v'] = float(parts[2])
                        telemetry_data['current_ma'] = float(parts[3])
                        telemetry_data['power_mw'] = float(parts[4])
                        telemetry_data['gain_pct'] = float(parts[5])
                        
                        timestamp = int(time.time() * 1_000_000)
                        csv_writer.writerow([
                            timestamp, telemetry_data['state_id'], telemetry_data['state'],
                            telemetry_data['voltage_v'], telemetry_data['current_ma'],
                            telemetry_data['power_mw'], telemetry_data['gain_pct']
                        ])
                        log_file.flush()
        except serial.SerialException as e:
            logger.error(f"Serial connection lost or error: {e}")
            logger.debug(traceback.format_exc())
            time.sleep(1) # Prevent CPU pegging on a dead port
        except Exception as e:
            logger.error(f"Unexpected error in serial thread: {e}")
            logger.debug(traceback.format_exc())
            
        time.sleep(0.005)

# -----------------------------------------------------------------------------
# HSV COLOR-TARGET SEGMENTATION
# -----------------------------------------------------------------------------
# White walls / glare have LOW saturation, so a high S_min rejects them outright,
# no matter how bright they are. OpenCV hue range is 0-179.
# Presets (H_min, H_max, S_min, S_max, V_min, V_max):
HSV_PRESETS = {
    'neon_green': (35, 85, 120, 255, 70, 255),
    'red':        (170, 10, 140, 255, 70, 255),  # H_min > H_max => hue wraps through 0
    'blue':       (95, 130, 140, 255, 60, 255),
}
ACTIVE_PRESET = 'neon_green'
MIN_AREA_PX = 500
MIN_SOLIDITY = 0.6           # rejects stringy/fragmented blobs (noise, edges)
_KERNEL = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))


def segment_color_target(frame, hsv_range):
    """Returns (primary_contour or None, binary_mask)."""
    h_lo, h_hi, s_lo, s_hi, v_lo, v_hi = hsv_range
    blurred = cv2.GaussianBlur(frame, (7, 7), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

    if h_lo <= h_hi:
        mask = cv2.inRange(hsv, (h_lo, s_lo, v_lo), (h_hi, s_hi, v_hi))
    else:
        # Hue wrap-around (e.g. red: H_min=170, H_max=10)
        m1 = cv2.inRange(hsv, (h_lo, s_lo, v_lo), (179, s_hi, v_hi))
        m2 = cv2.inRange(hsv, (0, s_lo, v_lo), (h_hi, s_hi, v_hi))
        mask = cv2.bitwise_or(m1, m2)

    # Open removes speckle noise, close fills holes in the card.
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, _KERNEL, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, _KERNEL, iterations=2)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    best, best_area = None, 0
    for c in contours:
        area = cv2.contourArea(c)
        if area < MIN_AREA_PX:
            continue
        hull_area = cv2.contourArea(cv2.convexHull(c))
        if hull_area <= 0 or (area / hull_area) < MIN_SOLIDITY:
            continue
        if area > best_area:
            best, best_area = c, area
    return best, mask


def main():
    logger.info("=== STARTING PROJECT A.R.C VISION PIPELINE ===")
    
    # 1. Serial Setup
    serial_port = find_serial_port()
    ser = None
    if serial_port:
        try:
            ser = serial.Serial(serial_port, 115200, timeout=0.1)
            logger.info(f"Successfully connected to ESP32 on {serial_port} at 115200 baud.")
        except serial.SerialException as e:
            logger.critical(f"Failed to open serial port {serial_port}: {e}")
            logger.debug(traceback.format_exc())
    else:
        logger.warning("Running without UART telemetry. ESP32 not detected.")

    # 2. CSV Logger Setup
    try:
        log_file = open(os.path.join(LOG_DIR, 'hitl_telemetry_log.csv'), 'w', newline='')
        csv_writer = csv.writer(log_file)
        csv_writer.writerow(['timestamp_us', 'state_id', 'state_name', 'voltage_v', 'current_ma', 'power_mw', 'gain_pct'])
        logger.debug("Initialized CSV telemetry logger.")
    except Exception as e:
        logger.critical(f"Failed to create CSV log file: {e}")
        logger.debug(traceback.format_exc())
        return

    # Start Listener Thread
    if ser is not None and ser.is_open:
        listener_thread = threading.Thread(target=serial_listener, args=(ser, csv_writer, log_file), daemon=True)
        listener_thread.name = "UART_RX_Thread"
        listener_thread.start()

    # 3. Webcam Initialization
    cap = None
    for vid in [0, 1, 2]:
        logger.debug(f"Attempting to open /dev/video{vid}...")
        # Force the V4L2 backend: opening by path string can pick a backend
        # (GStreamer/FFmpeg) that silently ignores cap.set() calls.
        cap = cv2.VideoCapture(vid, cv2.CAP_V4L2)
        if cap is not None and cap.isOpened():
            logger.info(f"Webcam successfully initialized on /dev/video{vid}")
            break
    
    if cap is None or not cap.isOpened():
        logger.critical("Could not open any webcam device. Aborting.")
        return

    # Order matters: FOURCC must be set BEFORE resolution, otherwise the driver
    # stays in its default YUYV 1920x1080 mode, which is capped at 5 fps.
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    fcc = int(cap.get(cv2.CAP_PROP_FOURCC))
    fcc_str = "".join(chr((fcc >> 8 * i) & 0xFF) for i in range(4))
    logger.info(f"Camera mode: {fcc_str} "
                f"{int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))} "
                f"@ {cap.get(cv2.CAP_PROP_FPS):.0f} fps")

    last_tx_time = time.time()
    tx_interval = 1.0 / 10.0  # 10 Hz TX
    
    dash = Dashboard(HSV_PRESETS, ACTIVE_PRESET)
    logger.info(f"HSV target preset: {ACTIVE_PRESET} {HSV_PRESETS[ACTIVE_PRESET]}")
    thresh = np.zeros((480, 640), dtype=np.uint8)
    tx_times = deque(maxlen=50)   # recent UART TX timestamps (for TX Hz readout)
    cam_fps, prev_frame_t = 20.0, time.time()

    logger.info("Entering main CV loop...")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                logger.error("Failed to grab frame from webcam. USB bandwidth drop, or device disconnected.")
                break

            H_frame, W_frame = frame.shape[:2]
            now = time.time()
            cam_fps = 0.9 * cam_fps + 0.1 * (1.0 / max(now - prev_frame_t, 1e-3))
            prev_frame_t = now

            try:
                primary_contour, thresh = segment_color_target(frame, dash.get_hsv())
            except Exception as e:
                logger.error(f"Error during image processing pipeline: {e}")
                logger.debug(traceback.format_exc())
                continue

            p_target = None
            t_run = 0.0

            if primary_contour is not None:
                x, y, w, h = cv2.boundingRect(primary_contour)
                cx = x + w / 2.0
                p_target = (cx / W_frame) * 100.0
                t_run = (p_target / 100.0) * 2.65

                telemetry_data['p_target'] = p_target
                telemetry_data['t_run'] = t_run

            # Mission-control dashboard (video overlay, FSM, telemetry, controls)
            now = time.time()
            tx_hz = sum(1 for t in tx_times if now - t <= 1.0)
            try:
                canvas = dash.render(frame, thresh, primary_contour, telemetry_data, {
                    'p_target': p_target, 't_run': t_run,
                    'serial_ok': ser is not None and ser.is_open,
                    'cam_fps': cam_fps, 'tx_hz': tx_hz,
                })
                dash.show(canvas)
            except Exception as e:
                logger.error(f"Error updating OpenCV UI: {e}")
                logger.debug(traceback.format_exc())

            current_time = time.time()
            if (current_time - last_tx_time) >= tx_interval:
                if p_target is not None and ser is not None and ser.is_open:
                    msg = f"P:{p_target:.2f}\n"
                    try:
                        ser.write(msg.encode('utf-8'))
                        logger.debug(f"SERIAL TX: {msg.strip()}")
                        tx_times.append(time.time())
                    except serial.SerialException as e:
                        logger.error(f"Failed to transmit UART packet: {e}")
                        logger.debug(traceback.format_exc())
                last_tx_time += tx_interval
                if current_time - last_tx_time > tx_interval:
                    last_tx_time = current_time  # resync after a stall

            if dash.handle_key(cv2.waitKey(1)):
                logger.info("User requested exit (pressed 'q').")
                break

    except KeyboardInterrupt:
        logger.warning("KeyboardInterrupt (Ctrl+C) caught. Shutting down gracefully...")
    except Exception as e:
        logger.critical(f"FATAL EXCEPTION in main loop: {e}")
        logger.debug(traceback.format_exc())
    finally:
        logger.info("Cleaning up resources...")
        cap.release()
        cv2.destroyAllWindows()
        if ser is not None and ser.is_open:
            ser.close()
        log_file.close()
        logger.info("Shutdown complete.")

if __name__ == '__main__':
    main()
