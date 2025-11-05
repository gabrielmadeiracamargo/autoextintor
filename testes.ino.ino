#include <Servo.h>
String inputString;
Servo left_right;
Servo up_down;

void setup() {
  left_right.attach(10);
  up_down.attach(9);
  Serial.begin(9600);
}

void loop() {
  while (Serial.available()) {
    inputString = Serial.readStringUntil('\r');

    if (inputString == "p") {
      Serial.println("🔥 Ativando modo de combate ao fogo!");
      continue;
    } else if (inputString == "s") {
      Serial.println("🚒 Fogo apagado - parando servos!");
      continue;
    }

    int commaIndex = inputString.indexOf(',');
    if (commaIndex > 0) {
      int x_axis = inputString.substring(0, commaIndex).toInt();
      int y_axis = inputString.substring(commaIndex + 1).toInt();

      int y = map(y_axis, 0, 1080, 180, 0);
      int x = map(x_axis, 0, 1920, 0, 180);

      left_right.write(x);
      up_down.write(y);

      Serial.print("X: "); Serial.println(x);
      Serial.print("Y: "); Serial.println(y);
    }
  }
}
