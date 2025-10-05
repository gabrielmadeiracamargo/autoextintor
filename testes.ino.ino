// Controle de LED via sinal do Python (OpenCV)
// Porta digital 2 -> LED

char data;  // variável para armazenar o dado recebido

void setup() {
  pinMode(2, OUTPUT);    // Define o pino 2 como saída
  digitalWrite(2, LOW);  // Garante que o LED inicie apagado
  Serial.begin(9600);    // Taxa de comunicação deve ser igual à do Python (9600)
}

void loop() {
  // Verifica se há dados disponíveis na serial
  if (Serial.available() > 0) {
    data = Serial.read();  // Lê o caractere recebido

    if (data == 'p') {
      digitalWrite(2, HIGH);  // Acende o LED
      Serial.println("🔥 Fogo detectado! LED ON");
    }
    else if (data == 's') {
      digitalWrite(2, LOW);   // Apaga o LED
      Serial.println("✅ Sem fogo. LED OFF");
    }
  }
}
