
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

client = mqtt.Client()

try:
    client.connect(BROKER_HOST, BROKER_PORT, 60)
except Exception as e:
    print(f"Не вдалося підключитися до {BROKER_HOST}:{BROKER_PORT}.")
    exit()


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


generator = generate_glucose()

print(f"device_id: {DEVICE_ID}")
print("Start! (Ctrl+C для зупинки)")

while True:

    current_level = next(generator)

    payload = {
        "device_id": DEVICE_ID,
        "level": current_level,
        "timestamp": datetime.now().isoformat(),
    }

    client.publish(TOPIC, json.dumps(payload), qos=1)
    print(f"Sent: {current_level} -> Port {BROKER_PORT}")

    time.sleep(5)