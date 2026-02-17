#define SOUND_PIN 34
#define RELAY_PIN 26

bool relayState = false;
bool lastSoundState = LOW;

void setup() {
  pinMode(SOUND_PIN, INPUT);
  pinMode(RELAY_PIN, OUTPUT);

  digitalWrite(RELAY_PIN, HIGH); // relay OFF initially

  Serial.begin(115200);
  Serial.println("System Ready...");
}

void loop() {
  // dito mo makikita yung pag get ng value ng digital using digitalRead(SOUND_PIN);
  // tapos ginawang soundstate int variables para sa true or false / 1 and 0 for binary 
  int soundState = digitalRead(SOUND_PIN);

  // if else logic for soundstate and laststate 
  if (soundState == HIGH && lastSoundState == LOW) {
    
    // relaystate = false then if not false then true the "!relayState" para kahit true or false value ok lang 
    // pwede din naman gumamit ng greater int value para sa greater and less example (relaystate = 1) -> condition if yung value is 1 and 0
    // approach mo kung paanong trip mo
    relayState = !relayState; // toggle state variables on and off

    if (relayState) {
      digitalWrite(RELAY_PIN, LOW);  // ON
      Serial.println("Sound detected → Relay ON"); // monitoring purpose
    } else {
      digitalWrite(RELAY_PIN, HIGH); // OFF
      Serial.println("Sound detected → Relay OFF"); // monitoring purpose 
    }

    delay(300); // debounce delay para di sunod sunod yung pag open open close open 
  }

  lastSoundState = soundState;
}
