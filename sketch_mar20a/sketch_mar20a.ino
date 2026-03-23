#include <LiquidCrystal_I2C.h>
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <ArduinoJson.h>


LiquidCrystal_I2C lcd(0x27, 16, 2);  // set the LCD address to 0x3F for a 16 chars and 2 line display

//Wifi Variables
const char* wifiSSD = "J-IOT";
const char* wifiPass = "Freak-2Thumb-Ghost!";

//Api Variables
const String apiURL = "http://api.imjoseph.com/v1/messages/";
const String apiKey = "";
unsigned long lastTime = 0;
unsigned long timerDelay = 5000;

// backup Messages
struct Message {
  const char* line_one;
  const char* line_two;
};

Message messages[] = {
  //{"                ", "                "},
  {"You look so very", "beutiful today  "},
  {"You are going to", "do so good today"},
  {"Your smile is so", "perfect         "},
  {"I think you are ", "so freaking cute"},
  {"I am so happy   ", "being yours     "},
  {"I am so very in ", "love with you   "},
  {"You are going to", "do great things "},
  {"All I want      ", "forever is you  "},
  {"Your eyes look  ", "so beutiful     "},
  {"I love your hair", "its so perfect  "},
  {"You are my life ", "line. I'm lucky "},
  {"I love your big ", "heart           "},
};

int messageCount = sizeof(messages) / sizeof(messages[0]);

// Print to LCD function
void lcdPrint(int row, int col, String message) {
  lcd.setCursor(col, row);
  lcd.print("                ");
  lcd.setCursor(col, row);
  lcd.print(message);
}

void setup() {
  Serial.begin(115200);

  lcd.init();
  lcd.clear();
  lcd.backlight();  // Make sure backlight is on

  // Setup Wifi
  WiFi.disconnect();
  delay(10);
  WiFi.mode(WIFI_STA);
  WiFi.begin(wifiSSD, wifiPass);
  lcdPrint(0, 0, "WiFi Connecting");

  while(WiFi.status() != WL_CONNECTED){
    lcdPrint(1,0, "Trying...");
    delay(100);
  }
  lcdPrint(1,0, "WiFi Connected");
 
}

void loop() {
  //fetch message
  if ((millis() - lastTime) > timerDelay) {
    lastTime = millis();
    //lcd.clear();
    if(WiFi.status()== WL_CONNECTED){
      WiFiClient client;
      HTTPClient http;
      http.begin(client, apiURL);
      http.addHeader("X-API-Key", apiKey);
      int httpCode = http.GET();

      if (httpCode == HTTP_CODE_OK) {
        String message = http.getString();
        JsonDocument doc;
        deserializeJson(doc, message);
        Serial.println(message);
        const char* lineOne = doc["line_one"];
        const char* lineTwo = doc["line_two"];
        lcdPrint(0,0, lineOne);
        lcdPrint(1,0, lineTwo);
        // Parse message and display on screen
      } else {
        Serial.printf("GET failed, error: %d\n", httpCode);
        // Print a message from the on board backup message library
        int messageIndex = random(messageCount);
        lcdPrint(0,0, messages[messageIndex].line_one);
        lcdPrint(1,0, messages[messageIndex].line_two);
        
      }
      http.end();
    }
  }
}