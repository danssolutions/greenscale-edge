#!/usr/bin/env python3
import time
import threading
import RPi.GPIO as GPIO


# ========================
# Pump Configuration
# ========================

PUMP_PIN = 12        # BCM numbering (GPIO12)
PWM_FREQ = 1000      # 1 kHz PWM (safe default)
DUTY_CYCLE = 75      # % ON time during the 20-second pumping phase
PUMP_ON_DURATION = 20       # seconds
PUMP_REST_DURATION = 300    # seconds (5 minutes)


# ========================
# Pump Worker Thread
# ========================

def pump_loop():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PUMP_PIN, GPIO.OUT)

    pwm = GPIO.PWM(PUMP_PIN, PWM_FREQ)
    pwm.start(0)

    print("[PUMP] Pump loop started.")

    try:
        while True:
            # Phase 1: Pump ON with duty cycle
            print(
                f"[PUMP] ON for {PUMP_ON_DURATION}s at {DUTY_CYCLE}% duty cycle")
            pwm.ChangeDutyCycle(DUTY_CYCLE)
            time.sleep(PUMP_ON_DURATION)

            # Phase 2: Pump OFF
            print(f"[PUMP] OFF for {PUMP_REST_DURATION}s")
            pwm.ChangeDutyCycle(0)
            time.sleep(PUMP_REST_DURATION)
    except KeyboardInterrupt:
        pass
    finally:
        print("[PUMP] Cleaning up GPIO")
        pwm.stop()
        GPIO.cleanup()


# def start_pump_thread():
#     """
#     Start pump_loop() in a daemon thread so it doesn't block main().
#     Call this once from main.py after boot.
#     """
#     t = threading.Thread(target=pump_loop, daemon=True)
#     t.start()
#     return t

if __name__ == "__main__":
    pump_loop()
