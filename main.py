import cv2
import numpy as np
import serial
import time
import sys
import os

# --- CONFIGURAÇÕES ---
PORTA = 'COM7'   # ajuste conforme necessário
BAUD = 9600
CASCADE_PATH = 'cascade.xml'

# --- VARIÁVEIS GLOBAIS ---
window_name = "🔥 Detecção de Fogo"
camera_opened = False
window_created = False

# --- SETUP SERIAL ---
try:
    ser = serial.Serial(PORTA, BAUD, timeout=1)
    time.sleep(2) # Espera o Arduino reiniciar
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    print(f"✅ Conectado ao Arduino em {PORTA}")
except serial.SerialException:
    print(f"⚠️ Não foi possível abrir {PORTA}. Rodando sem Arduino.")
    ser = None

# --- SETUP CÂMERA ---
cap = cv2.VideoCapture(0) # Tente index 1 se tiver mais de uma camera
if not cap.isOpened():
    print("❌ Erro: não foi possível acessar a câmera.")
    sys.exit(1)

# Forçar resolução (opcional, ajuda a manter estabilidade)
# cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
# cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

print("✅ Câmera aberta com sucesso.")
camera_opened = True

# --- SETUP CASCADE ---
fire_cascade = cv2.CascadeClassifier(CASCADE_PATH)
if fire_cascade.empty():
    print("❌ Erro: não foi possível carregar o cascade.xml.")
    sys.exit(1)

# --- VARIÁVEIS DE CONTROLE ---
fire_detected_frames = 0
fire_absent_frames = 0
last_fire_position = None
fire_confirmed = False
fire_lost = False

FRAME_THRESHOLD = 5         # Reduzi um pouco para ficar mais ágil
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

def send_coordinates(x_error, y_error):
    # Envia o ERRO (distância do centro)
    if ser:
        msg = f"{x_error},{y_error}\n"
        ser.write(msg.encode())
        # print(f"📡 Enviado: {msg.strip()}") # Comentei para não poluir o terminal
    else:
        print(f"Simulando envio: {x_error},{y_error}")

print("🎥 Sistema iniciado (ESC para sair)")

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("⚠️ Falha na captura de vídeo. Encerrando loop.")
            break

        # 1. PEGAR O CENTRO DA TELA DINAMICAMENTE
        height, width = frame.shape[:2]
        center_screen_x = width // 2
        center_screen_y = height // 2

        # Desenhar uma cruz no centro da tela (Referência)
        cv2.line(frame, (center_screen_x, 0), (center_screen_x, height), (255, 255, 0), 1)
        cv2.line(frame, (0, center_screen_y), (width, center_screen_y), (255, 255, 0), 1)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        fire = fire_cascade.detectMultiScale(gray, 1.2, 5)

        if len(fire) > 0:
            # Pega o maior fogo detectado (opcional: ordenar por área w*h)
            (x, y, w, h) = fire[0]
            
            # Desenha retângulo no fogo
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

            current_position = (x, y, w, h)

            # Lógica de persistência
            if is_same_position(current_position, last_fire_position, POSITION_TOLERANCE):
                fire_detected_frames += 1
                fire_absent_frames = 0
            else:
                fire_detected_frames = 1
                last_fire_position = current_position
                fire_absent_frames = 0

            # Se fogo confirmado
            if fire_detected_frames >= FRAME_THRESHOLD:
                if not fire_confirmed:
                    if ser: ser.write(b"p\n")
                    print("🔥 Fogo confirmado! Bomba ATIVADA.")
                    fire_confirmed = True

                # 2. CALCULAR O CENTRO DO FOGO
                fire_center_x = x + w // 2
                fire_center_y = y + h // 2

                # Desenhar ponto no centro do fogo
                cv2.circle(frame, (fire_center_x, fire_center_y), 5, (0, 255, 0), -1)

                # 3. MATEMÁTICA DO ERRO (0,0 é o centro da tela)
                error_x = fire_center_x - center_screen_x
                error_y = fire_center_y - center_screen_y

                # Desenhar linha do centro da tela até o fogo (Visualização do vetor erro)
                cv2.line(frame, (center_screen_x, center_screen_y), (fire_center_x, fire_center_y), (0, 255, 255), 2)

                # 4. ENVIAR APENAS O ERRO
                send_coordinates(error_x, error_y)
                
                fire_lost = False

        else:
            fire_absent_frames += 1
            if fire_absent_frames >= FIRE_ABSENCE_THRESHOLD:
                fire_lost = True

            if fire_lost and fire_confirmed:
                if ser: ser.write(b"s\n")
                print("🚒 Fogo apagado! Bomba DESLIGADA.")
                fire_confirmed = False
                fire_detected_frames = 0 # Resetar contador

        # Criar janela
        if not window_created:
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(window_name, 640, 480)
            window_created = True

        cv2.imshow(window_name, frame)

        key = cv2.waitKey(1) # Reduzi para 1ms para ficar mais fluido
        if key == 27:  # ESC
            print("👋 Encerrando...")
            break

except KeyboardInterrupt:
    print("⛔ Interrompido manualmente.")

finally:
    if ser and ser.is_open:
        # Tenta desligar a bomba antes de sair
        ser.write(b"s\n")
        ser.close()
    if camera_opened:
        cap.release()
    cv2.destroyAllWindows()
    print("✅ Recursos liberados.")
