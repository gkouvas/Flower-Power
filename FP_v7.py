import asyncio
import tkinter as tk
from tkinter import ttk
from bleak import BleakClient

# Replace with your Flower Power's MAC address
MAC_ADDRESS = "249214D9-57FB-0BBC-5F59-24EC9DDA4C0F"

# UUIDs for the characteristics corresponding to each measurement
CHARACTERISTIC_UUIDS = {
    "Soil Moisture": "39e1fa05-84a8-11e2-afba-0002a5d5c51b",
    "Fertilizer Level": "39e1fa02-84a8-11e2-afba-0002a5d5c51b",
    "Soil Temperature": "39e1fa03-84a8-11e2-afba-0002a5d5c51b",
    "Air Temperature": "39e1fa04-84a8-11e2-afba-0002a5d5c51b",
    "Light Intensity": "39e1fa01-84a8-11e2-afba-0002a5d5c51b",
}

# Calibration logic strictly from the publication
def calibrate_soil_moisture(raw_value):
    return max(0, (1.16 * (raw_value / 1000)) - 0.07)

def calibrate_fertilizer(raw_value):
    return raw_value * 0.001  # Scaling logic from the publication

def calibrate_temperature(raw_value):
    return raw_value / 32.0  # Celsius conversion from raw value

def calibrate_light_intensity(raw_value):
    return raw_value * 0.01  # Convert to mol/m²/day

# Conversion logic from MarkoMarjamaa's script
def convert_soil_moisture(raw_value):
    return raw_value / 32.0  # Example conversion

def convert_fertilizer(raw_value):
    return raw_value * 0.1  # Example conversion

def convert_temperature(raw_value):
    return raw_value / 32.0  # Matches calibrated value

def convert_light_intensity(raw_value):
    return raw_value * 0.01  # Same as calibrated

# Additional logic as per Achim Winkler's calculations
def calculate_value_achim(raw_value, label):
    if label == "Soil Moisture":
        return (raw_value / 256) * 10  # Example conversion
    elif label == "Fertilizer Level":
        return raw_value * 0.01
    elif label in ["Soil Temperature", "Air Temperature"]:
        return (raw_value - 500) / 10.0
    elif label == "Light Intensity":
        # Achim Winkler's sunlight conversion formula
        return ((raw_value * 1_000_000) / (3600 * 12)) * 54
    return raw_value

# Logic for "Correct Values" as per the document
def calculate_correct_value(raw_value, label):
    if label == "Light Intensity":
        return raw_value  # Light is raw_value directly
    elif label in ["Soil Moisture", "Fertilizer Level", "Soil Temperature", "Air Temperature"]:
        return (raw_value * 3.3) / (2**11 - 1)  # General formula for correct values
    return raw_value

async def read_and_display(ui_elements):
    print("Connecting to the Flower Power device...")
    try:
        async with BleakClient(MAC_ADDRESS, timeout=60.0) as client:
            print(f"Connected: {client.is_connected}")
            if not client.is_connected:
                raise Exception("Failed to connect to the device.")

            # Read and update UI for each characteristic
            for label, uuid in CHARACTERISTIC_UUIDS.items():
                try:
                    print(f"Reading {label}...")
                    value = await client.read_gatt_char(uuid)
                    if value:
                        raw_value = int.from_bytes(value, byteorder="little")
                        print(f"Raw {label}: {raw_value}")

                        # Calibrated values
                        if label == "Soil Moisture":
                            calibrated_value = calibrate_soil_moisture(raw_value)
                            converted_value = convert_soil_moisture(raw_value)
                        elif label == "Fertilizer Level":
                            calibrated_value = calibrate_fertilizer(raw_value)
                            converted_value = convert_fertilizer(raw_value)
                        elif label in ["Soil Temperature", "Air Temperature"]:
                            calibrated_value = calibrate_temperature(raw_value)
                            converted_value = convert_temperature(raw_value)
                        elif label == "Light Intensity":
                            calibrated_value = calibrate_light_intensity(raw_value)
                            converted_value = convert_light_intensity(raw_value)
                        else:
                            calibrated_value = raw_value
                            converted_value = raw_value

                        achim_value = calculate_value_achim(raw_value, label)
                        correct_value = calculate_correct_value(raw_value, label)

                        print(f"Calibrated {label} (Xaver): {calibrated_value}")
                        print(f"Converted {label} (MarkoMarjamaa): {converted_value}")
                        print(f"Calculated {label} (Achim Winkler): {achim_value}")
                        print(f"Correct {label} (Document): {correct_value}")

                        # Update the UI elements
                        ui_elements[label]["Raw Value"].set(f"{raw_value}")
                        ui_elements[label]["Value as per Xaver et al."].set(f"{calibrated_value:.2f}")
                        ui_elements[label]["Value as per MarkoMarjamaa"].set(f"{converted_value:.2f}")
                        ui_elements[label]["Value as per Achim Winkler"].set(f"{achim_value:.2f}")
                        ui_elements[label]["Correct Values"].set(f"{correct_value:.4f}")
                    else:
                        for col in ui_elements[label]:
                            ui_elements[label][col].set("No Data")
                except Exception as e:
                    print(f"Error reading {label}: {e}")
                    for col in ui_elements[label]:
                        ui_elements[label][col].set("Error")
    except Exception as e:
        print(f"Connection error: {e}")
        for label in ui_elements:
            for col in ui_elements[label]:
                ui_elements[label][col].set("Connection Error")

def setup_ui():
    # Create the main window
    root = tk.Tk()
    root.title("Flower Power Readings")
    root.geometry("1100x400")

    # UI elements for each characteristic
    ui_elements = {
        label: {
            "Raw Value": tk.StringVar(value="Waiting..."),
            "Value as per Xaver et al.": tk.StringVar(value="Waiting..."),
            "Value as per MarkoMarjamaa": tk.StringVar(value="Waiting..."),
            "Value as per Achim Winkler": tk.StringVar(value="Waiting..."),
            "Correct Values": tk.StringVar(value="Waiting..."),
        }
        for label in CHARACTERISTIC_UUIDS.keys()
    }

    # Table headers
    ttk.Label(root, text="Measurement", font=("Helvetica", 12, "bold")).grid(row=0, column=0, padx=10, pady=5, sticky="w")
    ttk.Label(root, text="Raw Value", font=("Helvetica", 12, "bold")).grid(row=0, column=1, padx=10, pady=5, sticky="w")
    ttk.Label(root, text="Value as per Xaver et al.", font=("Helvetica", 12, "bold")).grid(row=0, column=2, padx=10, pady=5, sticky="w")
    ttk.Label(root, text="Value as per MarkoMarjamaa", font=("Helvetica", 12, "bold")).grid(row=0, column=3, padx=10, pady=5, sticky="w")
    ttk.Label(root, text="Value as per Achim Winkler", font=("Helvetica", 12, "bold")).grid(row=0, column=4, padx=10, pady=5, sticky="w")
    ttk.Label(root, text="Correct Values", font=("Helvetica", 12, "bold")).grid(row=0, column=5, padx=10, pady=5, sticky="w")

    # Add rows for each measurement
    for i, (label, vars) in enumerate(ui_elements.items(), start=1):
        ttk.Label(root, text=label, font=("Helvetica", 10)).grid(row=i, column=0, padx=10, pady=5, sticky="w")
        ttk.Label(root, textvariable=vars["Raw Value"], font=("Helvetica", 10)).grid(row=i, column=1, padx=10, pady=5, sticky="w")
        ttk.Label(root, textvariable=vars["Value as per Xaver et al."], font=("Helvetica", 10)).grid(row=i, column=2, padx=10, pady=5, sticky="w")
        ttk.Label(root, textvariable=vars["Value as per MarkoMarjamaa"], font=("Helvetica", 10)).grid(row=i, column=3, padx=10, pady=5, sticky="w")
        ttk.Label(root, textvariable=vars["Value as per Achim Winkler"], font=("Helvetica", 10)).grid(row=i, column=4, padx=10, pady=5, sticky="w")
        ttk.Label(root, textvariable=vars["Correct Values"], font=("Helvetica", 10)).grid(row=i, column=5, padx=10, pady=5, sticky="w")

    # Refresh button
    async def on_refresh():
        await read_and_display(ui_elements)

    ttk.Button(root, text="Refresh", command=lambda: asyncio.run(on_refresh())).grid(
        row=len(ui_elements) + 1, column=0, columnspan=6, pady=10
    )

    return root

# Main entry point
if __name__ == "__main__":
    root = setup_ui()
    root.mainloop()