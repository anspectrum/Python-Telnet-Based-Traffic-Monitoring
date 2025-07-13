# This script is a quick traffic graph of tenda modem eth0 interface
import telnetlib
import time
import re
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from datetime import datetime

# ✅ Hardcoded configuration
HOST = "192.168.2.1"
USERNAME = "root"
PASSWORD = "Fireitup"
INTERFACE = "eth0"
INTERVAL = 5  # Sampling interval in seconds (change if needed)

# Cumulative byte counters
total_rx_bytes = 0
total_tx_bytes = 0
# Data storage
timestamps = []
rx_rates = []
tx_rates = []

# Telnet connection
print(f"Connecting to {HOST} via Telnet...")
tn = telnetlib.Telnet(HOST)
tn.read_until(b"login: ")
tn.write(USERNAME.encode('ascii') + b"\n")
tn.read_until(b"Password: ")
tn.write(PASSWORD.encode('ascii') + b"\n")
time.sleep(1)

# Function to get bytes from ifconfig
def get_ifconfig_bytes():
    tn.write(f"ifconfig {INTERFACE}\n".encode('ascii'))
    time.sleep(0.5)
    output = tn.read_very_eager().decode('ascii')
    rx_match = re.search(r'RX bytes:(\d+)', output)
    tx_match = re.search(r'TX bytes:(\d+)', output)
    if rx_match and tx_match:
        return int(rx_match.group(1)), int(tx_match.group(1))
    return None, None

# Initial values
prev_rx, prev_tx = get_ifconfig_bytes()
prev_time = time.time()

# Matplotlib animation update function
def update(frame):
    global prev_rx, prev_tx, prev_time
    global total_rx_bytes, total_tx_bytes

    curr_rx, curr_tx = get_ifconfig_bytes()
    curr_time = time.time()

    if curr_rx is None or curr_tx is None:
        print("Could not parse RX/TX. Skipping this interval...")
        return

    delta_time = curr_time - prev_time

    # Compute rates
    if curr_rx < prev_rx:
        rx_delta = curr_rx  # reset happened
    else:
        rx_delta = curr_rx - prev_rx

    if curr_tx < prev_tx:
        tx_delta = curr_tx  # reset happened
    else:
        tx_delta = curr_tx - prev_tx

    rx_rate = (rx_delta * 8) / delta_time / 1_000_000  # Mbps
    tx_rate = (tx_delta * 8) / delta_time / 1_000_000  # Mbps

    # Accumulate total bytes
    total_rx_bytes += rx_delta
    total_tx_bytes += tx_delta

    timestamp = datetime.now()
    timestamps.append(timestamp)
    rx_rates.append(rx_rate)
    tx_rates.append(tx_rate)

    # Trim old samples
    MAX_SAMPLES = 8640
    if len(timestamps) > MAX_SAMPLES:
        timestamps.pop(0)
        rx_rates.pop(0)
        tx_rates.pop(0)

    # Clear and replot
    ax.clear()
    ax.plot(timestamps, rx_rates, label='RX', color='blue')
    ax.plot(timestamps, tx_rates, label='TX', color='green')
    ax.set_title(f"Real-time Traffic on {INTERFACE}")
    ax.set_xlabel("Time")
    ax.set_ylabel("Mbps")
    ax.legend()
    ax.tick_params(axis='x', rotation=45)
    ax.grid(True)

    import matplotlib.dates as mdates
    ax.xaxis.set_major_locator(mdates.HourLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    fig.autofmt_xdate()

    # Format total data as MB or GB
    def format_bytes(num):
        if num > 1_000_000_000:
            return f"{num / 1_000_000_000:.2f} GB"
        return f"{num / 1_000_000:.2f} MB"

    rx_total_str = format_bytes(total_rx_bytes)
    tx_total_str = format_bytes(total_tx_bytes)

    # Add cumulative data info below the plot
    ax.text(0.01, -0.15, f"Total RX: {rx_total_str}", transform=ax.transAxes, fontsize=10, color='blue')
    ax.text(0.30, -0.15, f"Total TX: {tx_total_str}", transform=ax.transAxes, fontsize=10, color='green')

    plt.tight_layout()

    # Update previous values
    prev_rx, prev_tx = curr_rx, curr_tx
    prev_time = curr_time

# Set up plot
fig, ax = plt.subplots()
ani = animation.FuncAnimation(fig, update, interval=INTERVAL * 1000)

print("Showing live traffic graph. Close the window to stop.")
plt.show()

# Cleanup
tn.write(b"exit\n")
tn.close()
