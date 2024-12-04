import numpy as np
import time
import tkinter as tk
from tkinter import ttk

class VoltageQlearning:
    def __init__(self):
        self.nominal_voltages = [380, 110, 110]
        self.voltage_ranges = [(361, 399), (104.5, 115.5), (104.5, 115.5)]
        self.q_table = {}
        self.learning_rate = 0.1
        self.discount_factor = 0.95
        self.epsilon = 0.1

    def get_pu_values(self, voltages):
        return [v/n for v, n in zip(voltages, self.nominal_voltages)]

    def get_state(self, voltages):
        pu_values = self.get_pu_values(voltages)
        return tuple(round(pu, 3) for pu in pu_values)

    def calculate_reward(self, voltages):
        pu_values = self.get_pu_values(voltages)
        deviation = sum(abs(pu - 1.0) for pu in pu_values)
        return -deviation

    def select_action(self, state):
        if state not in self.q_table:
            self.q_table[state] = {(i,j,k): 0.0 
                                 for i in range(5) 
                                 for j in range(5) 
                                 for k in range(5)}
        
        if np.random.random() < self.epsilon:
            return tuple(np.random.randint(0, 5, 3))
        
        return max(self.q_table[state].items(), key=lambda x: x[1])[0]

    def update(self, state, action, reward, next_state):
        if next_state not in self.q_table:
            self.q_table[next_state] = {(i,j,k): 0.0 
                                      for i in range(5) 
                                      for j in range(5) 
                                      for k in range(5)}
        
        current_q = self.q_table[state][action]
        next_max_q = max(self.q_table[next_state].values())
        
        self.q_table[state][action] = current_q + self.learning_rate * (
            reward + self.discount_factor * next_max_q - current_q
        )

    def calculate_voltage_corrections(self, voltages):
        state = self.get_state(voltages)
        action = self.select_action(state)
        # Cambiado: si voltaje > nominal, sumar corrección; si voltaje < nominal, restar corrección
        corrections = []
        for v, nom in zip(voltages, self.nominal_voltages):
            tap = action[len(corrections)]
            correction = (tap - 2) * 2
            if v > nom:
                correction = abs(correction)  # Corrección positiva
            else:
                correction = -abs(correction)  # Corrección negativa
            corrections.append(correction)
            
        final_voltages = [v - c for v, c in zip(voltages, corrections)]
        
        next_state = self.get_state(final_voltages)
        reward = self.calculate_reward(final_voltages)
        self.update(state, action, reward, next_state)
        
        return corrections, action, final_voltages

class VoltageMonitor:
    def __init__(self):
        self.sensor_window = tk.Tk()
        self.sensor_window.title("Simulación de Sensores")
        self.monitor_window = tk.Toplevel()
        self.monitor_window.title("Monitor de Corrección")
        self.ql = VoltageQlearning()
        self.setup_sensor_window()
        self.setup_monitor_window()
    
    def setup_sensor_window(self):
        style = ttk.Style()
        style.configure('Custom.TEntry', padding=5)
        
        self.sensor_entries = []
        for i, v in enumerate([380, 110, 110]):
            frame = ttk.Frame(self.sensor_window)
            frame.pack(pady=5)
            ttk.Label(frame, text=f"Sensor {i+1} (V):").pack(side=tk.LEFT)
            entry = ttk.Entry(frame, width=10, style='Custom.TEntry')
            entry.insert(0, str(v))
            entry.pack(side=tk.LEFT, padx=5)
            self.sensor_entries.append(entry)
        
        ttk.Button(self.sensor_window, text="Actualizar valores", 
                  command=self.update_system).pack(pady=10)

    def setup_monitor_window(self):
        # Configurar la fuente para mejor legibilidad
        custom_font = ('Consolas', 10)
        
        # Frame superior para mostrar valores actuales
        current_frame = ttk.LabelFrame(self.monitor_window, text="Estado Actual", padding=10)
        current_frame.pack(fill='x', padx=5, pady=5)
        
        self.current_values_label = ttk.Label(current_frame, 
                                            text="Voltajes Medidos: --- | Valores PU: ---",
                                            font=custom_font)
        self.current_values_label.pack()

        # Frame para el historial
        history_frame = ttk.LabelFrame(self.monitor_window, text="Historial", padding=10)
        history_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.log_text = tk.Text(history_frame, height=10, width=70, font=custom_font)
        self.log_text.pack(fill='both', expand=True)
        
        # Frame para los taps
        taps_frame = ttk.LabelFrame(self.monitor_window, text="Estado de los TAPs", padding=10)
        taps_frame.pack(fill='x', padx=5, pady=5)
        
        self.tap_labels = []
        for i in range(3):
            label = ttk.Label(taps_frame, font=custom_font)
            label.pack(pady=2)
            self.tap_labels.append(label)

    def update_log(self, message):
        timestamp = time.strftime('%H:%M:%S')
        if " | " in message:
            # Es un mensaje de estado actual
            self.current_values_label.config(text=message)
        else:
            # Es un mensaje para el historial
            self.log_text.insert('1.0', f"{timestamp} - {message}\n")
            self.log_text.see('1.0')

    def update_system(self):
        try:
            voltages = [float(e.get()) for e in self.sensor_entries]
            corrections, actions, final_voltages = self.ql.calculate_voltage_corrections(voltages)
            
            pu_initial = self.ql.get_pu_values(voltages)
            pu_final = self.ql.get_pu_values(final_voltages)
            
            # Actualizar estado actual
            self.update_log(f"Voltajes Medidos: {voltages} | Valores PU: {[round(pu,3) for pu in pu_initial]}")
            
            # Actualizar historial
            self.update_log(f"Correcciones aplicadas: {[f'{c:+}V' for c in corrections]}")
            self.update_log(f"Voltajes finales: {[round(v,1) for v in final_voltages]} (PU: {[round(pu,3) for pu in pu_final]})")
            
            # Actualizar TAPs
            for i, (correction, action, final_v) in enumerate(zip(corrections, actions, final_voltages)):
                nominal = self.ql.nominal_voltages[i]
                self.tap_labels[i].config(
                    text=f"TAP {i+1}: {correction:+}V (Pos: {action}) → {round(final_v,1)}V | Nominal: {nominal}V | PU: {round(final_v/nominal,3)}"
                )
            
        except ValueError:
            self.update_log("Error: Ingrese valores numéricos válidos")

    def start(self):
        self.sensor_window.mainloop()

if __name__ == "__main__":
    monitor = VoltageMonitor()
    monitor.start()