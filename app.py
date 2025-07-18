from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import os
import signal
import subprocess
import threading
import time

app = Flask(__name__)

simulator_process = None
simulator_thread = None
is_running = False

def load_config():
    """Load configuration from config.json"""
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "broker": "mosquitto",
            "port": 1883,
            "client_id": "multi_line_sim",
            "random_seed": 42,
            "lines": {"1": 1, "2": 2, "3": 3, "4": 4},
            "tick_time": 1,
            "failure_probability": 0.1,
            "failure_status_min": 4,
            "failure_status_max": 6,
            "failure_duration_min": 30,
            "failure_duration_max": 120
        }

def save_config(config):
    """Save configuration to config.json"""
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=2)

def run_simulator():
    """Run the simulator in a separate thread"""
    global simulator_process, is_running
    try:
        simulator_process = subprocess.Popen(['python', 'counter.py'])
        is_running = True
        simulator_process.wait()
    except Exception as e:
        print(f"Error running simulator: {e}")
    finally:
        is_running = False

def stop_simulator():
    """Stop the simulator process"""
    global simulator_process, is_running
    if simulator_process:
        simulator_process.terminate()
        simulator_process.wait()
        simulator_process = None
    is_running = False

@app.route('/')
def index():
    """Main page with current settings and controls"""
    config = load_config()
    return render_template('index.html', config=config, is_running=is_running)

@app.route('/update_config', methods=['POST'])
def update_config():
    """Update configuration from form data"""
    config = load_config()
    
    config['broker'] = request.form.get('broker', config['broker'])
    config['port'] = int(request.form.get('port', config['port']))
    config['client_id'] = request.form.get('client_id', config['client_id'])
    config['random_seed'] = int(request.form.get('random_seed', config['random_seed']))
    
    config['tick_time'] = float(request.form.get('tick_time', config.get('tick_time', 1)))
    config['failure_probability'] = float(request.form.get('failure_probability', config.get('failure_probability', 0.1)))
    config['failure_status_min'] = int(request.form.get('failure_status_min', config.get('failure_status_min', 4)))
    config['failure_status_max'] = int(request.form.get('failure_status_max', config.get('failure_status_max', 6)))
    config['failure_duration_min'] = int(request.form.get('failure_duration_min', config.get('failure_duration_min', 30)))
    config['failure_duration_max'] = int(request.form.get('failure_duration_max', config.get('failure_duration_max', 120)))
    
    lines = {}
    for key in request.form.keys():
        if key.startswith('line_') and key.endswith('_cells'):
            line_num = key.split('_')[1]
            cell_count = int(request.form.get(key, 1))
            lines[line_num] = cell_count
    
    config['lines'] = lines
    save_config(config)
    return redirect(url_for('index'))

@app.route('/start_simulator', methods=['POST'])
def start_simulator():
    """Start the simulator"""
    global simulator_thread, is_running
    if not is_running:
        simulator_thread = threading.Thread(target=run_simulator)
        simulator_thread.daemon = True  
        simulator_thread.start()
        time.sleep(1)  
    return redirect(url_for('index'))

@app.route('/stop_simulator', methods=['POST'])
def stop_simulator_route():
    """Stop the simulator"""
    stop_simulator()
    return redirect(url_for('index'))

@app.route('/status')
def status():
    """API endpoint to check simulator status"""
    return jsonify({'is_running': is_running})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=19033, debug=True)