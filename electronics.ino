#include <Servo.h>

#define PUMP_PIN 5
#define RES_X_HALF 960 
#define RES_Y_HALF 540 

// EIXO Y (Vertical) - Mantido simétrico
#define Y_CENTER_SERVO 75
#define Y_RANGE_SERVO 30 

String inputString;
Servo left_right;
Servo up_down;

void setup() {
  left_right.attach(10);
  up_down.attach(11);

  pinMode(PUMP_PIN, OUTPUT);
  digitalWrite(PUMP_PIN, LOW);

  Serial.begin(9600);
  delay(1000);

  left_right.write(45); 
  up_down.write(Y_CENTER_SERVO);  

  while (Serial.available()) Serial.read();
  Serial.println("OK");
}

void loop() {
  if (Serial.available()) {
    
    inputString = Serial.readStringUntil('\n');
    inputString.trim(); 

    if (inputString == "p") {
      digitalWrite(PUMP_PIN, HIGH);
      return;
    }
    if (inputString == "s") {
      digitalWrite(PUMP_PIN, LOW);
      return;
    }

    if (inputString.length() < 2) return;

    int commaIndex = inputString.indexOf(',');
    if (commaIndex < 1) return;

    int x_error = inputString.substring(0, commaIndex).toInt();
    int y_error = inputString.substring(commaIndex + 1).toInt();

    int val_x;

    // --- INICIO DO TRECHO ALTERADO ---
    // INVERSÃO REALIZADA: Trocamos os destinos do map()
    if (x_error < 0) {
      // Antes era 0->45, agora vai para o lado oposto (135->45)
      // Lado Esquerdo da tela aciona ângulos maiores (fisicamente Direita ou vice-versa)
      val_x = map(x_error, -RES_X_HALF, 0, 135, 45);
    } else {
      // Antes era 45->135, agora vai para o lado oposto (45->0)
      // Lado Direito da tela aciona ângulos menores
      val_x = map(x_error, 0, RES_X_HALF, 45, 0); 
    }
    val_x = constrain(val_x, 0, 135);
    // --- FIM DO TRECHO ALTERADO ---

    int y_min_servo = Y_CENTER_SERVO - Y_RANGE_SERVO;
    int y_max_servo = Y_CENTER_SERVO + Y_RANGE_SERVO;

    int val_y = map(y_error, -RES_Y_HALF, RES_Y_HALF, y_max_servo, y_min_servo); 
    val_y = constrain(val_y, y_min_servo, y_max_servo);

    left_right.write(val_x-10);
    up_down.write(val_y);
  }
}
