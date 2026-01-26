
### Цей код не використовуєтся у застосунку безпосередньо
# Він запускається сторонньо від проєкту для симуляції пристрою,
# що надсилає показники глюкози шляхом MQTT повідомлень
# Доданий для фіксації коду симуляції пристрою у Git

import paho.mqtt.client as mqtt
import json
import time
import random
from datetime import datetime


BROKER_HOST = "localhost"
BROKER_PORT = 1884
TOPIC = "devices/glucose"
DEVICE_ID = "7877"
SUB_TOPIC=f"devices/{DEVICE_ID}/commands"

client = mqtt.Client()

try:
    client.connect(BROKER_HOST, BROKER_PORT, 60)
except Exception as e:
    print(f"Не вдалося підключитися до {BROKER_HOST}:{BROKER_PORT}.")
    exit()

def on_connect(client, userdata, flags, rc):
    client.subscribe(SUB_TOPIC)
    print(f"Пристрій підключено! Слухаю команди в: {SUB_TOPIC}")


def on_message(client, userdata, msg):
    try:
        command_data = json.loads(msg.payload.decode())
        print(f"Отримано команду: {command_data}")

        if command_data.get("action") == "measure_now":
            send_measurement(client)
        else:
            print("Невідома команда")

    except Exception as e:
        print(f"Помилка обробки команди: {e}")


def send_measurement(client):
    current_level = next(generator)
    payload = {
        "device_id": DEVICE_ID,
        "level": current_level,
        "timestamp": datetime.now().isoformat(),
    }
    client.publish(TOPIC, json.dumps(payload), qos=1)
    print(f"EXtra sent: {current_level} -> Port {BROKER_PORT}")

def generate_glucose():
    level = 4.8
    trend = 0.1
    while True:
        if random.random() > 0.8:
            trend = random.uniform(-0.3, 0.3)

        level += trend

        if level > 14: trend = -0.3
        if level < 3: trend = 0.3

        yield round(level, 1)


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
generator = generate_glucose()

try:
    client.connect(BROKER_HOST, BROKER_PORT, 60)
except Exception as e:
    print(f"Не вдалося підключитися.")
    exit()

# фоновий потік для прослуховування команд
client.loop_start()

print(f"Пристрій {DEVICE_ID} працює. (Ctrl+C для зупинки)")

try:
    while True:
        current_level = next(generator)

        payload = {
            "device_id": DEVICE_ID,
            "level": current_level,
            "timestamp": datetime.now().isoformat(),
        }

        client.publish(TOPIC, json.dumps(payload), qos=1)
        print(f"Sent: {current_level} -> Port {BROKER_PORT}")

        time.sleep(30)

except KeyboardInterrupt:
    print("Зупинка.")
    client.loop_stop()
    client.disconnect()