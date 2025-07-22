from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import numpy as np

app = Flask(__name__)
CORS(app)

def simulate_buck_converter(vin, duty_cycle, inductance, capacitance, resistance, frequency):
    # Convert inputs to SI units
    L = inductance * 1e-6  # µH to H
    C = capacitance * 1e-6  # µF to F
    R = resistance  # Ω
    f = frequency * 1e3  # kHz to Hz
    T = 1 / f  # Period in seconds

    # Steady-state calculations
    vout = vin * duty_cycle  # Ideal output voltage
    iout = vout / R  # Output current
    delta_il = (vin - vout) * duty_cycle * T / L  # Inductor current ripple

    # Time array for one period
    num_points = 1000
    t = np.linspace(0, T * 1e3, num_points)  # Time in ms
    voltage = np.ones(num_points) * vout
    current = np.zeros(num_points)

    # Simulate inductor current (triangular waveform)
    t_on = duty_cycle * T
    for i, ti in enumerate(t * 1e-3):  # Convert ms to s
        if ti % T < t_on:
            # Switch on: inductor current ramps up
            current[i] = iout - delta_il/2 + (vin - vout) * (ti % T) / L
        else:
            # Switch off: inductor current ramps down
            current[i] = iout + delta_il/2 - vout * (ti % T - t_on) / L

    # Add capacitor voltage ripple (simplified)
    delta_v = delta_il / (8 * C * f)
    voltage += delta_v * np.sin(2 * np.pi * f * t * 1e-3)

    return t.tolist(), voltage.tolist(), current.tolist()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/simulate', methods=['POST'])
def simulate():
    try:
        data = request.get_json()
        vin = float(data['vin'])
        duty_cycle = float(data['dutyCycle'])
        inductance = float(data['inductance'])
        capacitance = float(data['capacitance'])
        resistance = float(data['resistance'])
        frequency = float(data['frequency'])

        if not (0 <= duty_cycle <= 1) or vin <= 0 or inductance <= 0 or capacitance <= 0 or resistance <= 0 or frequency <= 0:
            return jsonify({'error': 'Invalid input parameters'}), 400

        time, voltage, current = simulate_buck_converter(vin, duty_cycle, inductance, capacitance, resistance, frequency)
        return jsonify({'time': time, 'voltage': voltage, 'current': current})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)