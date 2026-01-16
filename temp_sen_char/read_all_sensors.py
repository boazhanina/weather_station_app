#!/usr/bin/env python3

import time
import statistics
import sys
import glob

from sensor_map import SENSOR_MAP

BASE_DIR = "/sys/bus/w1/devices"
SENSOR_GLOB = BASE_DIR + "/28-*"
SLEEP_BETWEEN_ITERATIONS = 0.1  # 100 ms


def read_temp(sensor_path):
    """
    Read temperature from DS18B20 w1_slave file.
    Returns temperature in Celsius (float) or None on failure.
    """
    try:
        with open(sensor_path + "/w1_slave", "r") as f:
            lines = f.readlines()

        if lines[0].strip().endswith("YES"):
            temp_str = lines[1].split("t=")[-1]
            return float(temp_str) / 1000.0
        else:
            return None

    except Exception as e:
        print(f"[ERROR] Failed to read sensor file {sensor_path}: {e}")
        return None


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 read_all_sensors_debug.py <iterations>")
        sys.exit(1)

    iterations = int(sys.argv[1])

    sensors = sorted(glob.glob(SENSOR_GLOB))

    if not sensors:
        print("[ERROR] No DS18B20 sensors found.")
        sys.exit(1)

    print(f"[INFO] Found {len(sensors)} sensors on the bus:")
    for s in sensors:
        serial = s.split("/")[-1]
        index = next((i for i, sn in SENSOR_MAP.items() if sn == serial), None)
        print(f"  - index={index} serial={serial}")

    measurements = {
        serial: []
        for serial in SENSOR_MAP.values()
    }

    print(f"\n[INFO] Starting measurement loop ({iterations} iterations)")
    print("-" * 70)

    for i in range(iterations):
        print(f"[ITERATION {i + 1}/{iterations}] Starting")

        for index, serial in SENSOR_MAP.items():
            sensor_path = f"{BASE_DIR}/{serial}"
            print(f"  [READ] Sensor index={index} serial={serial} ...", end=" ")

            temp = read_temp(sensor_path)

            if temp is None:
                print("FAILED")
            else:
                print(f"OK -> {temp:.3f} °C")
                measurements[serial].append(temp)

        print(f"[ITERATION {i + 1}] Done, sleeping {int(SLEEP_BETWEEN_ITERATIONS * 1000)} ms\n")
        time.sleep(SLEEP_BETWEEN_ITERATIONS)

    print("\n" + "=" * 70)
    print("FINAL STATISTICS PER SENSOR")
    print("=" * 70)

    for index, serial in SENSOR_MAP.items():
        values = measurements.get(serial, [])

        if not values:
            print(f"index={index} serial={serial} | NO VALID MEASUREMENTS")
            continue

        min_t = min(values)
        max_t = max(values)
        avg_t = sum(values) / len(values)
        med_t = statistics.median(values)

        print(
            f"index={index} | "
            f"serial={serial} | "
            f"min={min_t:.3f} °C | "
            f"max={max_t:.3f} °C | "
            f"avg={avg_t:.3f} °C | "
            f"median={med_t:.3f} °C | "
            f"samples={len(values)}"
        )

    print("\n[INFO] Script finished successfully.")


if __name__ == "__main__":
    main()

