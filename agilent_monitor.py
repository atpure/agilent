import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import serial
import serial.tools.list_ports
import threading
import time
import csv
from datetime import datetime

class AgilentE3632AApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Agilent E3632A Debug Monitor")
        self.root.geometry("600x500")

        self.serial_port = None
        self.running = False
        self.data_log = []

        self.setup_ui()

    def setup_ui(self):
        config_frame = ttk.LabelFrame(self.root, text="Connection Settings", padding=10)
        config_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(config_frame, text="Port:").grid(row=0, column=0, padx=5)
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(config_frame, textvariable=self.port_var)
        self.port_combo.grid(row=0, column=1, padx=5)
        self.refresh_ports()

        self.refresh_btn = ttk.Button(config_frame, text="Refresh", command=self.refresh_ports)
        self.refresh_btn.grid(row=0, column=2, padx=5)

        control_frame = ttk.Frame(self.root, padding=10)
        control_frame.pack(fill="x", padx=10, pady=5)

        self.start_btn = ttk.Button(control_frame, text="Start", command=self.start_monitoring)
        self.start_btn.pack(side="left", padx=5)

        self.stop_btn = ttk.Button(control_frame, text="Stop", command=self.stop_monitoring, state="disabled")
        self.stop_btn.pack(side="left", padx=5)

        self.clear_btn = ttk.Button(control_frame, text="Clear", command=self.clear_logs, state="normal")
        self.clear_btn.pack(side="left", padx=5)

        self.export_btn = ttk.Button(control_frame, text="Export CSV", command=self.export_csv)
        self.export_btn.pack(side="left", padx=5)

        log_frame = ttk.LabelFrame(self.root, text="Data Log", padding=10)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Create scrollbar first to reserve space, then text widget
        self.scrollbar = ttk.Scrollbar(log_frame, orient="vertical")
        self.scrollbar.pack(side="right", fill="y")

        self.log_text = tk.Text(log_frame, height=15, yscrollcommand=self.scrollbar.set)
        self.log_text.pack(side="left", fill="both", expand=False)

        # Configure scrollbar command after both widgets are created
        self.scrollbar.config(command=self.log_text.yview)

    def refresh_ports(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combo['values'] = ports
        if ports: self.port_combo.current(0)

    def format_value(self, value_str):
        try:
            return f"{float(value_str):.3f}"
        except:
            return "0.000"

    def start_monitoring(self):
        port = self.port_var.get()
        print(f"\n[DEBUG] Connecting to {port}...") # Debug
        
        try:
            self.serial_port = serial.Serial(
                port=port, baudrate=9600, timeout=3, # Extended timeout to 3 seconds
                dsrdtr=False, rtscts=False
            )
            print(f"[DEBUG] Port {port} opened successfully.")

            # IDN verification (device connection test)
            print("[DEBUG] Sending *IDN? query...")
            self.serial_port.write(b"*IDN?\r\n")
            time.sleep(0.5)
            idn = self.serial_port.readline().decode().strip()
            
            if idn:
                print(f"[DEBUG] Device Identified: {idn}")
            else:
                print("[DEBUG] No response to *IDN?. Check cable/baudrate.")
                # Proceed even without response, but print warning

            print("[DEBUG] Setting to Remote Mode...")
            self.serial_port.write(b"SYST:REM\r\n")
            time.sleep(0.2)

            self.running = True
            self.start_btn.config(state="disabled")
            self.stop_btn.config(state="normal")
            self.clear_btn.config(state="disabled")
            self.export_btn.config(state="disabled")
            
            self.monitor_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
            self.monitor_thread.start()
            # print("[DEBUG] Monitoring thread started.")

        except Exception as e:
            print(f"[DEBUG] Connection Failed: {e}")
            messagebox.showerror("Error", str(e))

    def monitoring_loop(self):
        print("[DEBUG] Entering Loop...")
        while self.running:
            try:
                # Voltage
                # print("[DEBUG] Querying Voltage...")
                self.serial_port.write(b"MEAS:VOLT?\r\n")
                time.sleep(0.2)
                v_line = self.serial_port.readline().decode().strip()
                # print(f"[DEBUG] Voltage Recv: '{v_line}'")

                # Current
                # print("[DEBUG] Querying Current...")
                self.serial_port.write(b"MEAS:CURR?\r\n")
                time.sleep(0.2)
                c_line = self.serial_port.readline().decode().strip()
                # print(f"[DEBUG] Current Recv: '{c_line}'")

                if v_line and c_line:
                    now = datetime.now().strftime("%H:%M:%S")
                    fv, fc = self.format_value(v_line), self.format_value(c_line)
                    self.data_log.append([now, fv, fc])
                    self.root.after(0, self.update_log_ui, f"[{now}] V: {fv}, A: {fc}\n")
                
                time.sleep(0.6)

            except Exception as e:
                print(f"[DEBUG] Loop Exception: {e}")
                break
        print("[DEBUG] Loop Finished.")

    def stop_monitoring(self):
        print("[DEBUG] Stopping...")
        self.running = False
        time.sleep(1)
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(b"SYST:LOC\r\n")
            self.serial_port.close()
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.clear_btn.config(state="normal")
        self.export_btn.config(state="normal")

    def clear_logs(self):
        """Clear both log window and data log"""
        self.log_text.delete(1.0, tk.END)  # Delete all content from text widget
        self.data_log.clear()  # Also clear data log list

    def export_csv(self):
        """Save data log as CSV file"""
        if not self.data_log:
            messagebox.showwarning("Warning", "No data to export.")
            return

        # File save dialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save as CSV file"
        )

        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # Write header
                    writer.writerow(['Time', 'Voltage (V)', 'Current (A)'])
                    
                    # Write data
                    for row in self.data_log:
                        writer.writerow(row)
                
                messagebox.showinfo("Success", f"CSV file saved successfully:\n{filename}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error saving CSV file:\n{str(e)}")

    def update_log_ui(self, text):
        self.log_text.insert(tk.END, text)
        self.log_text.see(tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = AgilentE3632AApp(root)
    root.mainloop()
