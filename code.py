import board
from digitalio import DigitalInOut, Direction, Pull
import displayio
import rotaryio
import time
import wifi
import socketpool
import select
import alarm
import supervisor
import adafruit_imageload as imageload

from airtub import pack_data, unpack_data
from secrets import secrets


# constrain the temperature to 35-60
def constrain(value, min_value, max_value):
    return max(min(value, max_value), min_value)


# change pallete color
def change_color(value):
    if value < 40:
        return 0xFFFFFF  # 白色
    if value < 50:
        return 0xFFA500  # 橙色
    return 0xFF0000  # 红色


# update_temperature
def update_temperature(points):
    temperature[1] = points % 10
    temperature[0] = (points // 10) % 10


# send command to airtub_partner
def setDhwTemp(socket, myname, target, password, msg_type, value):
    message = f'{{"tar":"{target}","dev":"{myname}","tdt":{value},"sta":1}}'
    send_message = pack_data(msg_type, message, password)
    try:
        socket.sendto(send_message, (unicast_host, port))
    except BrokenPipeError:
        print("Connection closed by the other side")


# define msg_type and ttl
msg_type = 3  # 1:airtub 2:airtemp 3:aircube 4:airmon 5:airlog
port = 4211
unicast_host = secrets["device"] + ".local"

data_buffer = bytearray(256)
data_buffer_m = bytearray(256)

# define alarm
pin_alarm = alarm.pin.PinAlarm(board.IO21, pull=True, value=False)

# define rotary encoder
encoder = rotaryio.IncrementalEncoder(board.IO42, board.IO41)
last_position = 0
temperature_setpoint = 45

# read from alarm_memory
if alarm.wake_alarm:
    temperature_setpoint = alarm.sleep_memory[0]

# define button
button = DigitalInOut(board.IO40)
button.direction = Direction.INPUT
button.pull = Pull.UP
last_state = button.value

# init airtub communication
try:
    wifi.radio.connect(ssid=secrets["ssid"], password=secrets["password"])
    print("my ip addr:", str(wifi.radio.ipv4_address))
    pool = socketpool.SocketPool(wifi.radio)
    sock = pool.socket(pool.AF_INET, pool.SOCK_DGRAM)
    sock.connect((unicast_host, port))
    sock.setblocking(False)
    sock.settimeout(0)
except OSError as e:
    print("Unable to initialize the network", e)
    time.sleep(2)
    supervisor.reload()

board.DISPLAY.refresh(target_frames_per_second=60)
# screen.rotation = 270  # button on the left-hand
group = displayio.Group(scale=4)

# Load digital (temperature) bitmap
digital_bmp, palette = imageload.load(
    "/airtub/digital200x25.bmp", bitmap=displayio.Bitmap, palette=displayio.Palette
)
palette.make_transparent(1)
palette[0] = 0xFFFFFF
temperature = displayio.TileGrid(
    digital_bmp, pixel_shader=palette, width=2, height=1, tile_width=20, tile_height=25
)
temperature.x = 10
temperature.y = 4
group.append(temperature)


board.DISPLAY.root_group = group
board.DISPLAY.refresh(target_frames_per_second=60)

poller = select.poll()
poller.register(sock, select.POLLIN)
command_send = False

counter = 0

while True:
    if poller.poll(0) and command_send:
        try:
            size, addr = sock.recvfrom_into(data_buffer)
            if size > 0:
                dataid, datalen, realdata, crc1, crc2 = unpack_data(
                    data_buffer, size, secrets["devpass"]
                )
                if crc1 == crc2 and secrets["device"] in realdata:
                    print("command received")
                    command_send = False

        except OSError:
            pass

    elif command_send:
        print("resend...")
        setDhwTemp(
            sock,
            secrets["myname"],
            secrets["device"],
            secrets["devpass"],
            msg_type,
            temperature_setpoint,
        )

    current_state = button.value
    if current_state != last_state:
        if current_state:
            print("Button released!")
            counter = 0
        else:
            print("Button pressed!")
            command_send = True
            setDhwTemp(
                sock,
                secrets["myname"],
                secrets["device"],
                secrets["devpass"],
                msg_type,
                temperature_setpoint,
            )
        last_state = current_state
    current_position = encoder.position
    position_change = current_position - last_position
    if position_change != 0:
        counter = 0
    last_position = current_position
    temperature_setpoint += position_change
    temperature_setpoint = constrain(temperature_setpoint, 35, 60)
    update_temperature(temperature_setpoint)
    palette[0] = change_color(temperature_setpoint)
    temperature.pixel_shader = palette
    counter += 0.005
    if counter >= 10:
        alarm.sleep_memory[0] = temperature_setpoint
        time.sleep(2)
        alarm.exit_and_deep_sleep_until_alarms(pin_alarm)
    time.sleep(0.005)
