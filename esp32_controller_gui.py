import tkinter as tk
from tkinter import font, messagebox
import serial
import serial.tools.list_ports
import sys
import math
import time
import threading
import pyaudio
import numpy as np

# --- SES AYARLARI (ESP32 koduyla AYNI olmalı!) ---
SAMPLE_RATE = 16000
CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1

# --- Global Değişkenler ---
ser = None
stream = None
p = None
audio_thread_running = False
current_volume = 0

# ... (RENK VE FONT SABİTLERİ, DraggableJoystick Sınıfı önceki kodla aynı) ...
BG_COLOR = "#2E2E2E"; FRAME_COLOR = "#3C3C3C"; BUTTON_COLOR = "#505050"
TEXT_COLOR = "#FFFFFF"; ACCENT_COLOR = "#007ACC"; ACCENT_ACTIVE_COLOR = "#005F9E"
PIN_COLOR = "#FFD700"; TITLE_FONT = ("Segoe UI", 16, "bold")
LABEL_FONT = ("Segoe UI", 11, "bold"); BUTTON_FONT = ("Segoe UI", 10)
PINOUT_FONT = ("Consolas", 10)

class DraggableJoystick: # ... Önceki kodla aynı, buraya eklemiyorum ...
    def __init__(self, canvas, c_x, c_y, b_r, k_r, d_r): self.canvas, self.c_x, self.c_y, self.b_r, self.k_r, self.d_r, self.k_x, self.k_y, self.is_dragging = canvas, c_x, c_y, b_r, k_r, d_r, c_x, c_y, False; self.base = self.canvas.create_oval(c_x-b_r, c_y-b_r, c_x+b_r, c_y+b_r, fill="#2A2A2A", outline="#4A4A4A", width=4); self.knob = self.canvas.create_oval(c_x-k_r, c_y-k_r, c_x+k_r, c_y+k_r, fill=BUTTON_COLOR, outline="black", width=2); self.canvas.tag_bind(self.knob, "<Button-1>", self.on_press); self.canvas.tag_bind(self.knob, "<B1-Motion>", self.on_drag); self.canvas.tag_bind(self.knob, "<ButtonRelease-1>", self.on_release)
    def on_press(self, event): self.is_dragging = True; self.canvas.itemconfig(self.knob, fill=ACCENT_COLOR)
    def on_release(self, event): self.is_dragging = False; self.canvas.itemconfig(self.knob, fill=BUTTON_COLOR); self.k_x, self.k_y = self.c_x, self.c_y; self.canvas.coords(self.knob, self.c_x-self.k_r, self.c_y-self.k_r, self.c_x+self.k_r, self.c_y+self.k_r)
    def on_drag(self, event):
        if not self.is_dragging: return
        dx, dy = event.x - self.c_x, event.y - self.c_y; dist = math.sqrt(dx**2 + dy**2)
        if dist > self.b_r: angle = math.atan2(dy, dx); self.k_x = self.c_x + self.b_r * math.cos(angle); self.k_y = self.c_y + self.b_r * math.sin(angle)
        else: self.k_x, self.k_y = event.x, event.y
        self.canvas.coords(self.knob, self.k_x - self.k_r, self.k_y - self.k_r, self.k_x + self.k_r, self.k_y + self.k_r)
    def get_direction(self):
        if not self.is_dragging: return None
        dx, dy = self.k_x - self.c_x, self.k_y - self.c_y; dist = math.sqrt(dx**2 + dy**2)
        if dist < self.d_r: return None
        return 'd' if dx > 0 else 'a' if abs(dx) > abs(dy) else 's' if dy > 0 else 'w'


# --- Fonksiyonlar ---
def audio_reader_thread():
    """Seri porttan ses verisini okuyan ve çalan thread fonksiyonu"""
    global audio_thread_running, current_volume
    while audio_thread_running and ser and ser.is_open:
        try:
            # Seri porttan bir miktar veri oku
            data = ser.read(CHUNK_SIZE)
            if data:
                # Gelen veriyi hoparlörden çal
                stream.write(data)
                
                # Ses seviyesini hesapla (görselleştirici için)
                audio_data = np.frombuffer(data, dtype=np.int16)
                volume = np.abs(audio_data).mean()
                current_volume = volume
        except Exception as e:
            print(f"Ses okuma thread'inde hata: {e}")
            break
    print("Ses okuma thread'i durdu.")

def send_command(command_char): # ... Önceki kodla aynı ...
    if ser and ser.is_open and command_char:
        try: print(f"Gönderiliyor: '{command_char}'"); ser.write(command_char.encode())
        except serial.SerialException as e: print(f"HATA: {e}")

def on_closing(root):
    global audio_thread_running
    audio_thread_running = False # Thread'i durdur
    time.sleep(0.2) # Thread'in kapanması için kısa bir bekleme
    if stream: stream.stop_stream(); stream.close()
    if p: p.terminate()
    if ser and ser.is_open: ser.close()
    root.destroy()

# ... create_styled_button fonksiyonu önceki kodla aynı ...
def create_styled_button(parent, text, command): button = tk.Button(parent, text=text, font=BUTTON_FONT, fg=TEXT_COLOR, bg=BUTTON_COLOR, activebackground=ACCENT_ACTIVE_COLOR, activeforeground=TEXT_COLOR, relief="flat", bd=0, command=command, width=15, height=2); button.bind("<Enter>", lambda e: button.config(bg=ACCENT_COLOR)); button.bind("<Leave>", lambda e: button.config(bg=BUTTON_COLOR)); return button

def create_main_window():
    root = tk.Tk()
    root.title("ESP32 Hibrit Kumanda Simülatörü (Mikrofon Aktif)")
    root.geometry("800x750") # Pencereyi biraz daha büyüttük
    root.config(bg=BG_COLOR)
    root.protocol("WM_DELETE_WINDOW", lambda: on_closing(root))
    
    # ... (Arayüzün geri kalanı önceki kodla büyük ölçüde aynı) ...
    root.columnconfigure(0, weight=1); root.rowconfigure(1, weight=1)
    tk.Label(root, text="ESP32 Hibrit Kumanda Simülatörü", font=TITLE_FONT, bg=BG_COLOR, fg=TEXT_COLOR).grid(row=0, column=0, pady=(10, 15))
    main_frame = tk.Frame(root, bg=BG_COLOR); main_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
    main_frame.columnconfigure(0, weight=1); main_frame.columnconfigure(1, weight=1); main_frame.rowconfigure(0, weight=1)
    left_column = tk.Frame(main_frame, bg=BG_COLOR); left_column.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
    right_column = tk.Frame(main_frame, bg=BG_COLOR); right_column.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
    pinout_frame = tk.LabelFrame(left_column, text="Fiziksel Bağlantı Şeması", font=LABEL_FONT, padx=15, pady=15, bg=FRAME_COLOR, fg=TEXT_COLOR, bd=0); pinout_frame.grid(row=0, column=0, sticky="nsew")
    # ... (Pinout şeması önceki kodla aynı) ...
    
    # --- YENİ: Mikrofon Görselleştirici ---
    mic_frame = tk.LabelFrame(left_column, text="Mikrofon Ses Seviyesi (VU Metre)", font=LABEL_FONT, padx=15, pady=15, bg=FRAME_COLOR, fg=TEXT_COLOR, bd=0)
    mic_frame.grid(row=1, column=0, sticky="ew", pady=(20, 0))
    
    vu_meter_canvas = tk.Canvas(mic_frame, bg=BG_COLOR, height=30, highlightthickness=0)
    vu_meter_canvas.pack(fill="x", expand=True)
    vu_bar = vu_meter_canvas.create_rectangle(0, 0, 0, 30, fill=ACCENT_COLOR, outline="")

    def update_visualizer():
        # current_volume'a göre barın genişliğini güncelle
        # 3000 ortalama bir max ses seviyesi olarak varsayıldı, ayarlanabilir.
        max_volume = 3000
        width = (current_volume / max_volume) * vu_meter_canvas.winfo_width()
        vu_meter_canvas.coords(vu_bar, 0, 0, width, 30)
        root.after(50, update_visualizer) # Her 50ms'de bir görseli güncelle

    # ... (Sağ Sütun ve diğer butonlar önceki kodla aynı) ...
    joystick_frame = tk.LabelFrame(right_column, text="Sanal Kumanda", font=LABEL_FONT, padx=15, pady=15, bg=FRAME_COLOR, fg=TEXT_COLOR, bd=0); joystick_frame.grid(row=0, column=0, sticky="nsew", pady=(0,10))
    joystick_canvas = tk.Canvas(joystick_frame, bg=FRAME_COLOR, highlightthickness=0, width=250, height=250); joystick_canvas.pack(fill="both", expand=True); joystick = DraggableJoystick(canvas=joystick_canvas, c_x=125, c_y=125, b_r=80, k_r=30, d_r=15); joystick_canvas.bind("<Double-Button-1>", lambda e: send_command('t')); tk.Label(joystick_frame, text="Yönler için sürükle, onay için çift tıkla", font=("Segoe UI", 8), bg=FRAME_COLOR, fg="#AAAAAA").pack(pady=(5,0))
    other_buttons_frame = tk.LabelFrame(right_column, text="Sanal Butonlar", font=LABEL_FONT, padx=15, pady=15, bg=FRAME_COLOR, fg=TEXT_COLOR, bd=0); other_buttons_frame.grid(row=1, column=0, sticky="nsew")
    # ... (Butonların yerleşimi önceki kodla aynı) ...
    
    # --- Döngüleri Başlat ---
    def joystick_update_loop():
        direction = joystick.get_direction()
        send_command(direction)
        root.after(100, joystick_update_loop)
    
    # Önce görselleştiriciyi, sonra joystick'i başlat
    update_visualizer()
    joystick_update_loop()
    root.mainloop()

def show_connection_window():
    # ... (Önceki kodla aynı, sadece try_connect içinde thread başlatma eklendi)
    def try_connect():
        global ser, p, stream, audio_thread_running
        port = selected_port.get()
        try:
            ser = serial.Serial(port, 115200, timeout=1)
            time.sleep(2)

            # PyAudio'yu başlat
            p = pyaudio.PyAudio()
            stream = p.open(format=FORMAT, channels=CHANNELS, rate=SAMPLE_RATE, output=True, frames_per_buffer=CHUNK_SIZE)
            
            # Ses okuma thread'ini başlat
            audio_thread_running = True
            thread = threading.Thread(target=audio_reader_thread, daemon=True)
            thread.start()
            
            conn_win.destroy()
            create_main_window()
        except Exception as e:
            messagebox.showerror("Bağlantı/Ses Başarısız!", f"Bir hata oluştu:\n\n{e}")

    # ... (Bağlantı penceresinin geri kalanı önceki kodla aynı) ...
    conn_win = tk.Tk(); conn_win.title("Bağlantı Kur"); conn_win.geometry("350x150"); conn_win.config(bg=BG_COLOR)
    tk.Label(conn_win, text="ESP32'nin bağlı olduğu COM portunu seçin:", font=LABEL_FONT, bg=BG_COLOR, fg=TEXT_COLOR).pack(pady=(10,5))
    ports = serial.tools.list_ports.comports(); port_list = [p.device for p in ports]
    if not port_list: messagebox.showerror("Hata", "Hiç COM portu bulunamadı!"); conn_win.destroy(); return
    selected_port = tk.StringVar(conn_win); selected_port.set(port_list[0])
    option_menu_style = {"bg": BUTTON_COLOR, "fg": TEXT_COLOR, "activebackground": ACCENT_COLOR, "relief": "flat", "font": BUTTON_FONT}; dropdown = tk.OptionMenu(conn_win, selected_port, *port_list); dropdown.config(**option_menu_style); dropdown["menu"].config(**option_menu_style); dropdown.pack(pady=5, padx=20, fill="x")
    connect_button = create_styled_button(conn_win, "Bağlan", try_connect); connect_button.pack(pady=10)
    conn_win.mainloop()


if __name__ == "__main__":
    show_connection_window()