from hiibot_iots2 import IoTs2
import board
from digitalio import DigitalInOut, Direction, Pull
import displayio
import rotaryio
import time
import wifi
import socketpool
import adafruit_imageload as imageload

from airtub import pack_data
from secrets import secrets

# define msg_type and ttl
msg_type = 3  # 1:airtub 2:airtemp 3:aircube 4:airmon 5:airlog
multicast_port = 4211
multicast_group = "224.0.1.3"

# define rotary encoder
encoder = rotaryio.IncrementalEncoder(board.IO42, board.IO41)
last_position = 0
temperature_setpoint = 45

# define button
button = DigitalInOut(board.IO40)
button.direction = Direction.INPUT
button.pull = Pull.UP
last_state = button.value

# init airtub communication
wifi.radio.connect(ssid=secrets["ssid"], password=secrets["password"])
print("my ip addr:", wifi.radio.ipv4_address)
pool = socketpool.SocketPool(wifi.radio)
sock = pool.socket(pool.AF_INET, pool.SOCK_DGRAM)

screen = IoTs2().screen
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
def setDhwTemp(socket, myname, target, password, value):
    message = f'{{"tar":"{target}","dev":"{myname}","tdt":{value},"sta":1}}'
    send_message = pack_data(msg_type, message, password)
    try:
        socket.settimeout(0)
        socket.sendto(send_message, (multicast_group, multicast_port))
    except BrokenPipeError:
        print("Connection closed by the other side")


screen.show(group)

while True:
    current_state = button.value
    if current_state != last_state:
        if current_state:
            print("Button released!")
        else:
            print("Button pressed!")
            setDhwTemp(
                sock,
                secrets["myname"],
                secrets["device"],
                secrets["devpass"],
                temperature_setpoint,
            )
        last_state = current_state
    current_position = encoder.position
    position_change = current_position - last_position
    last_position = current_position
    temperature_setpoint += position_change
    temperature_setpoint = constrain(temperature_setpoint, 35, 60)
    update_temperature(temperature_setpoint)
    palette[0] = change_color(temperature_setpoint)
    temperature.pixel_shader = palette
    screen.show(group)
    time.sleep(0.005)
