# Запит на пристрій на термінову перевірку цукора
# Запускається окремо від проєкту, надсилає одноразовий
# запит та завершує роботу.
import paho.mqtt.client as mqtt
import json

BROKER_HOST = "localhost"
BROKER_PORT = 1884
DEVICE_ID = "7877"
COMMAND_TOPIC = f"devices/{DEVICE_ID}/commands"


def trigger_measurement():
    client = mqtt.Client()

    try:
        client.connect(BROKER_HOST, BROKER_PORT, 60)
        client.loop_start()
        command = {
            "action": "measure_now"
        }

        info = client.publish(COMMAND_TOPIC, json.dumps(command), qos=1)
        info.wait_for_publish()
        print(f"Запит 'measure_now' надіслано в {COMMAND_TOPIC}")
        client.disconnect()
    except Exception as e:
        print(f"Не вдалося надіслати запит: {e}")

if __name__ == "__main__":
    trigger_measurement()