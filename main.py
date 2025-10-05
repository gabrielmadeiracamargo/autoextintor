import numpy as np
import cv2
import serial
import time

fire_cascade = cv2.CascadeClassifier('cascade.xml')

ser1 = serial.Serial('COM9', 9600)

cap = cv2.VideoCapture(0)

fire_detected_frames = 0
fire_absent_frames = 0
last_fire_position = None
fire_confirmed = False
fire_lost = False

FRAME_THRESHOLD = 10  # 1 segundo se o vídeo for 10 FPS
POSITION_TOLERANCE = 50  # tolerância para considerar mesma posição
FIRE_ABSENCE_THRESHOLD = 20  # número de frames sem fogo para confirmar que apagou

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

while cap.isOpened():
    ret, img = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    fire = fire_cascade.detectMultiScale(img, 12, 5)

    if len(fire) > 0:
        # Considerando apenas o primeiro foco de fogo detectado
        (x, y, w, h) = fire[0]
        current_position = (x, y, w, h)
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 2)

        if is_same_position(current_position, last_fire_position, POSITION_TOLERANCE):
            fire_detected_frames += 1
            fire_absent_frames = 0  # Reseta a contagem de ausência do fogo
        else:
            fire_detected_frames = 1  # Reinicia contagem
            last_fire_position = current_position
            fire_absent_frames = 0  # Reseta a contagem de ausência do fogo

        if fire_detected_frames >= FRAME_THRESHOLD and not fire_confirmed:
            print('🔥 Fogo confirmado após 3 segundos!')
            ser1.write(str.encode('p'))
            fire_confirmed = True

        fire_lost = False  # Se o fogo está visível, não consideramos que ele foi perdido

    else:
        fire_absent_frames += 1
        if fire_absent_frames >= FIRE_ABSENCE_THRESHOLD:
            fire_lost = True

        # Se o fogo foi perdido e não está mais sendo confirmado, envia o sinal
        if fire_lost and fire_confirmed:
            print('🚒 Fogo apagado!')
            ser1.write(str.encode('s'))
            fire_confirmed = False  # Reseta a confirmação

    cv2.imshow('img', img)

    if cv2.waitKey(100) & 0xFF == 27:  # ESC para sair
        break

ser1.close()
cap.release()
cv2.destroyAllWindows()
