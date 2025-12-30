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
        self.root.title("Agilent E3632A Monitor")
        self.root.geometry("600x500")

        self.serial_port = None
        self.running = False
        self.data_log = []

        self.setup_ui()

    def setup_ui(self):
        # Configuration Frame
        config_frame = ttk.LabelFrame(self.root, text="Connection Settings", padding=10)
        config_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(config_frame, text="Port:").grid(row=0, column=0, padx=5)
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(config_frame, textvariable=self.port_var)
        self.port_combo.grid(row=0, column=1, padx=5)
        self.refresh_ports()

        self.refresh_btn = ttk.Button(config_frame, text="Refresh", command=self.refresh_ports)
        self.refresh_btn.grid(row=0, column=2, padx=5)

        # Control Frame
        control_frame = ttk.Frame(self.root, padding=10)
        control_frame.pack(fill="x", padx=10, pady=5)

        self.start_btn = ttk.Button(control_frame, text="Start", command=self.start_monitoring)
        self.start_btn.pack(side="left", padx=5)

        self.stop_btn = ttk.Button(control_frame, text="Stop", command=self.stop_monitoring, state="disabled")
        self.stop_btn.pack(side="left", padx=5)

        self.export_btn = ttk.Button(control_frame, text="Export CSV", command=self.export_csv)
        self.export_btn.pack(side="left", padx=5)

        # Log Frame
        log_frame = ttk.LabelFrame(self.root, text="Data Log (Time, Voltage, Current)", padding=10)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.log_text = tk.Text(log_frame, height=15)
        self.log_text.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=scrollbar.set)

    def refresh_ports(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combo['values'] = ports
        if ports:
            self.port_combo.current(0)

    def format_value(self, value_str):
        """전압/전류 값을 포맷팅: 음수일 때만 - 부호, 소수점 4자리 반올림 후 3자리 표시"""
        try:
            value = float(value_str)
            # 소수점 4자리에서 반올림
            rounded_value = round(value, 4)
            
            # 양수인 경우 부호 없이, 음수인 경우 - 부호 포함 (소수점 3자리까지 표시)
            if rounded_value >= 0:
                return f"{rounded_value:.3f}"
            else:
                return f"{rounded_value:.3f}"  # 음수이면 - 부호 자동 포함
        except ValueError:
            return value_str  # 변환 실패시 원본 값 반환

    def start_monitoring(self):
        port = self.port_var.get()
        if not port:
            messagebox.showerror("Error", "Please select a COM port")
            return

        try:
            # RS-232 settings for Agilent E3632A
            # Default: 9600 baud, 8 data bits, no parity, 1 stop bit, DTR/DSR flow control
            self.serial_port = serial.Serial(
                port=port,
                baudrate=9600,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=2,             # 응답 대기 시간 (초)
                xonxoff=False,
                rtscts=False,
                dsrdtr=True
            )
            
            # Identify device
            self.serial_port.write(b"*IDN?\n")
            idn = self.serial_port.readline().decode().strip()
            print(f"Connected to: {idn}")
            
            # Put in remote mode
            self.serial_port.write(b"SYST:REM\n")

            self.running = True
            self.data_log = []
            self.log_text.delete(1.0, tk.END)
            
            self.start_btn.config(state="disabled")
            self.stop_btn.config(state="normal")
            self.port_combo.config(state="disabled")

            self.monitor_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
            self.monitor_thread.start()

        except Exception as e:
            messagebox.showerror("Connection Error", str(e))
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()

    def stop_monitoring(self):
        self.running = False
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.write(b"SYST:LOC\n") # Return to local mode
                self.serial_port.close()
            except:
                pass
        
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.port_combo.config(state="normal")

    def monitoring_loop(self):
        while self.running:
            try:
                # Query Voltage
                self.serial_port.write(b"MEAS:VOLT?\n")
                volt = self.serial_port.readline().decode().strip()
                
                # Query Current
                self.serial_port.write(b"MEAS:CURR?\n")
                curr = self.serial_port.readline().decode().strip()

                if volt and curr:
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # 전압과 전류 값을 포맷팅
                    formatted_volt = self.format_value(volt)
                    formatted_curr = self.format_value(curr)
                    
                    # 포맷팅된 값을 로그에 저장
                    log_entry = [now, formatted_volt, formatted_curr]
                    self.data_log.append(log_entry)
                    
                    display_text = f"[{now}] V: {formatted_volt}, A: {formatted_curr}\n"
                    self.root.after(0, self.update_log_ui, display_text)

                time.sleep(1)
            except Exception as e:
                print(f"Loop Error: {e}")
                self.running = False
                self.root.after(0, lambda: messagebox.showerror("Error", f"Communication lost: {e}"))
                self.root.after(0, self.stop_monitoring)
                break

    def update_log_ui(self, text):
        self.log_text.insert(tk.END, text)
        self.log_text.see(tk.END)

    def export_csv(self):
        if not self.data_log:
            messagebox.showwarning("Warning", "No data to export")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"E3632A_Log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )

        if file_path:
            try:
                with open(file_path, mode='w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Timestamp", "Voltage (V)", "Current (A)"])
                    writer.writerows(self.data_log)
                messagebox.showinfo("Success", f"Data exported to {file_path}")
            except Exception as e:
                messagebox.showerror("Export Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = AgilentE3632AApp(root)
    root.mainloop()
