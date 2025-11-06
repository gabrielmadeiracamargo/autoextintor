import cv2
import numpy as np
import serial
import time
import sys
import os

# --- CONFIGURAÇÕES ---
PORTA = 'COM9'  # ajuste conforme sua porta serial
BAUD = 9600
CASCADE_PATH = 'cascade.xml'

# --- VARIÁVEIS GLOBAIS ---
window_name = "🔥 Detecção de Fogo"
camera_opened = False
window_created = False

# --- SETUP SERIAL ---
try:
    ser = serial.Serial(PORTA, BAUD, timeout=1)
    time.sleep(2)
    print(f"✅ Conectado ao Arduino em {PORTA}")
except serial.SerialException:
    print(f"⚠️ Não foi possível abrir {PORTA}. Rodando sem Arduino.")
    ser = None

# --- SETUP CÂMERA (somente uma vez) ---
if not camera_opened:
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Erro: não foi possível acessar a câmera.")
        sys.exit(1)
    else:
        print("✅ Câmera aberta com sucesso.")
        camera_opened = True

# --- SETUP CASCADE ---
fire_cascade = cv2.CascadeClassifier(CASCADE_PATH)
if fire_cascade.empty():
    print("❌ Erro: não foi possível carregar o cascade.xml.")
    sys.exit(1)

# --- VARIÁVEIS ---
fire_detected_frames = 0
fire_absent_frames = 0
last_fire_position = None
fire_confirmed = False
fire_lost = False

FRAME_THRESHOLD = 10
POSITION_TOLERANCE = 50
FIRE_ABSENCE_THRESHOLD = 20

def is_same_position(pos1, pos2, tolerance):
    if pos1 is None or pos2 is None:
        return False
    x1, y1, w1, h1 = pos1
    x2, y2, w2, h2 = pos2
    return (
        abs(x1 - x2) < tolerance and
        abs(y1 - y2) < tolerance and
        abs(w1 - w2) < tolerance and
        abs(h1 - h2) < tolerance
    )

def send_coordinates(x, y):
    if ser:
        msg = f"{x},{y}\n"
        ser.write(msg.encode())
        print(f"📡 Enviado ao Arduino: {msg.strip()}")
    else:
        print(f"Simulando envio: {x},{y}")

print("🎥 Sistema iniciado (ESC para sair)")

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("⚠️ Falha na captura de vídeo. Encerrando loop.")
            break

        fire = fire_cascade.detectMultiScale(frame, 12, 5)

        if len(fire) > 0:
            (x, y, w, h) = fire[0]
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

            current_position = (x, y, w, h)
            if is_same_position(current_position, last_fire_position, POSITION_TOLERANCE):
                fire_detected_frames += 1
                fire_absent_frames = 0
            else:
                fire_detected_frames = 1
                last_fire_position = current_position
                fire_absent_frames = 0

            if fire_detected_frames >= FRAME_THRESHOLD and not fire_confirmed:
                if ser:
                    ser.write(b"p\n")
                    print("🔥 Fogo confirmado!")
                fire_confirmed = True

            if fire_confirmed:
                fire_center_x = x + w // 2
                fire_center_y = y + h // 2
                send_coordinates(fire_center_x, fire_center_y)

            fire_lost = False
        else:
            fire_absent_frames += 1
            if fire_absent_frames >= FIRE_ABSENCE_THRESHOLD:
                fire_lost = True

            if fire_lost and fire_confirmed:
                if ser:
                    ser.write(b"s\n")
                    print("🚒 Fogo apagado!")
                fire_confirmed = False

        # Cria a janela só uma vez
        if not window_created:
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(window_name, 640, 480)
            window_created = True

        # Atualiza a janela existente
        cv2.imshow(window_name, frame)

        key = cv2.waitKey(50)
        if key == 27:  # ESC
            print("👋 Encerrando...")
            break

except KeyboardInterrupt:
    print("⛔ Interrompido manualmente.")

finally:
    if ser and ser.is_open:
        ser.close()
    if camera_opened:
        cap.release()
    cv2.destroyAllWindows()
    print("✅ Recursos liberados e janela fechada.")
