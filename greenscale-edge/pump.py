#!/usr/bin/env python3
import time
import RPi.GPIO as GPIO

# ========================
# Pump Configuration
# ========================

PUMP_PIN = 12             # BCM pin number (GPIO12)
PWM_FREQ = 1000           # Hz
DUTY_CYCLE = 100           # % duty during active phase
PUMP_ON_DURATION = 20     # seconds
PUMP_REST_DURATION = 300  # seconds (5 min)


def pump_loop():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PUMP_PIN, GPIO.OUT)

    pwm = GPIO.PWM(PUMP_PIN, PWM_FREQ)
    pwm.start(0)

    print("[PUMP] Pump loop started.")
    try:
        while True:
            # Active phase
            print(f"[PUMP] ON for {PUMP_ON_DURATION}s at {DUTY_CYCLE}% duty")
            pwm.ChangeDutyCycle(DUTY_CYCLE)
            time.sleep(PUMP_ON_DURATION)

            # Rest phase
            print(f"[PUMP] OFF for {PUMP_REST_DURATION}s")
            pwm.ChangeDutyCycle(0)
            time.sleep(PUMP_REST_DURATION)
    except KeyboardInterrupt:
        print("[PUMP] Interrupted, cleaning up GPIO.")
    finally:
        pwm.stop()
        GPIO.cleanup()
        print("[PUMP] GPIO cleaned up, exiting.")


def main():
    pump_loop()


if __name__ == "__main__":
    main()
