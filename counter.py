import time
import random
import json
import paho.mqtt.client as mqtt

# Load configuration from config.json
def load_config():
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: config.json file not found!")
        exit(1)
    except json.JSONDecodeError:
        print("Error: Invalid JSON in config.json!")
        exit(1)

# Load configuration
config = load_config()

# Extract configuration values
broker = config.get("broker", "localhost")
port = config.get("port", 18883)
client_id = config.get("client_id", "multi_line_sim")
seed = config.get("random_seed", 42)
lines = config.get("lines", {1: 1, 2: 2, 3: 3, 4: 4})
tick_time = config.get("tick_time", 1)
failure_probability = config.get("failure_probability", 0.1)
failure_status_min = config.get("failure_status_min", 4)
failure_status_max = config.get("failure_status_max", 6)
failure_duration_min = config.get("failure_duration_min", 30)
failure_duration_max = config.get("failure_duration_max", 120)

# Initialize MQTT client
client = mqtt.Client(client_id=client_id, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
client.connect(broker, port, 60)

# Set random seed
random.seed(seed)

# Initialize cells based on lines configuration
cells = {}
for line, cell_count in lines.items():
    for cell in range(1, cell_count + 1):
        key = f"line{line}_cell{cell}"
        cells[key] = {
            "I": 0,
            "status": 1,
            "status_timer": 0,
            "status_duration": 0,
        }

# Main simulation loop
while True:
    for key, state in cells.items():
        line, cell = key.split("_")
        topic_base = f"yourMomsBakery/someArea/{line}/{cell}/edge"
        
        if state["status"] == 1:
            if random.random() < failure_probability:
                state["status"] = random.randint(failure_status_min, failure_status_max)
                duration_seconds = random.randint(failure_duration_min, failure_duration_max)
                state["status_duration"] = int(duration_seconds / tick_time)
                state["status_timer"] = 0
            else:
                infeed = state["I"]
                outfeed = infeed - 2 if infeed >= 2 else 0
                reject = infeed - outfeed if infeed > outfeed else 0
                client.publish(f"{topic_base}/infeed", infeed)
                client.publish(f"{topic_base}/outfeed", outfeed)
                client.publish(f"{topic_base}/reject", reject)
                print(f"[{line}/{cell}] status: 1 | infeed: {infeed}, outfeed: {outfeed}, reject: {reject}")
                state["I"] += 1
        else:
            print(f"[{line}/{cell}] status: {state['status']}")
            state["status_timer"] += 1
            if state["status_timer"] >= state["status_duration"]:
                state["status"] = 1
                state["status_timer"] = 0
                state["status_duration"] = 0
        
        client.publish(f"{topic_base}/status", state["status"])
    
    time.sleep(tick_time)