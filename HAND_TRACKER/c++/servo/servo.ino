#include <Servo.h>

Servo servo;

void setup() {
  Serial.begin(115200);
  servo.attach(13);  // signal pin
}

void loop() {
  if (Serial.available()) {
    char cmd = Serial.read();
    if (cmd == 'U') servo.write(180);
    else if (cmd == 'D') servo.write(0);
  }
}
