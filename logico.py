import tkinter as tk
from tkinter import ttk
import time

class VoltageControl:
    def __init__(self):
        self.nominal_voltages = [380, 110, 110]
        self.voltage_ranges = [(361, 399), (104.5, 115.5), (104.5, 115.5)]
        self.tap_step = 2  # Voltios por paso del TAP
        self.max_taps = 5  # Número de posiciones del TAP

    def get_pu_values(self, voltages):
        return [v/n for v, n in zip(voltages, self.nominal_voltages)]

    def calculate_corrections(self, voltages):
        corrections = []
        actions = []
        
        for i, (voltage, nominal) in enumerate(zip(voltages, self.nominal_voltages)):
            error = voltage - nominal
            
            # Determinar número de pasos necesarios
            steps = min(abs(error) // self.tap_step, self.max_taps - 1)
            tap_position = int(steps)
            
            if error > 0:
                correction = self.tap_step * tap_position
            else:
                correction = -self.tap_step * tap_position
                
            corrections.append(correction)
            actions.append(tap_position)
            
        final_voltages = [v - c for v, c in zip(voltages, corrections)]
        return corrections, actions, final_voltages

class VoltageMonitor:
    def __init__(self):
        self.sensor_window = tk.Tk()
        self.sensor_window.title("Control de Voltaje - Lógico")
        self.monitor_window = tk.Toplevel()
        self.monitor_window.title("Monitor de Corrección")
        self.vc = VoltageControl()
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
        custom_font = ('Consolas', 10)
        
        current_frame = ttk.LabelFrame(self.monitor_window, text="Estado Actual", padding=10)
        current_frame.pack(fill='x', padx=5, pady=5)
        self.current_values_label = ttk.Label(current_frame, 
                                            text="Voltajes Medidos: --- | Valores PU: ---",
                                            font=custom_font)
        self.current_values_label.pack()

        history_frame = ttk.LabelFrame(self.monitor_window, text="Historial", padding=10)
        history_frame.pack(fill='both', expand=True, padx=5, pady=5)
        self.log_text = tk.Text(history_frame, height=10, width=70, font=custom_font)
        self.log_text.pack(fill='both', expand=True)
        
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
            self.current_values_label.config(text=message)
        else:
            self.log_text.insert('1.0', f"{timestamp} - {message}\n")
            self.log_text.see('1.0')

    def update_system(self):
        try:
            voltages = [float(e.get()) for e in self.sensor_entries]
            corrections, actions, final_voltages = self.vc.calculate_corrections(voltages)
            
            pu_initial = self.vc.get_pu_values(voltages)
            pu_final = self.vc.get_pu_values(final_voltages)
            
            self.update_log(f"Voltajes Medidos: {voltages} | Valores PU: {[round(pu,3) for pu in pu_initial]}")
            self.update_log(f"Correcciones aplicadas: {[f'{c:+}V' for c in corrections]}")
            self.update_log(f"Voltajes finales: {[round(v,1) for v in final_voltages]} (PU: {[round(pu,3) for pu in pu_final]})")
            
            for i, (correction, action, final_v) in enumerate(zip(corrections, actions, final_voltages)):
                nominal = self.vc.nominal_voltages[i]
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