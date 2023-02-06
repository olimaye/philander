from smbus import SMBus
import time

i2c = SMBus(1)

# Chip address
device_address = 0x40

CMD_GET_TEMP_HOLD  = 0xE3
CMD_GET_HUM_HOLD   = 0xE5
CMD_GET_TEMP       = 0xF3
CMD_GET_HUM        = 0xF5
CMD_WRITE_USR_REG  = 0xE6
CMD_READ_USR_REG   = 0xE7
CMD_RESET          = 0xFE

USR_RESOLUTION     = 0x81
USR_RESOLUTION_RH12_T14 = 0x00
USR_RESOLUTION_RH8_T12  = 0x01
USR_RESOLUTION_RH10_T13 = 0x80
USR_RESOLUTION_RH11_T11 = 0x81
USR_RESOLUTION_DEFAULT  = USR_RESOLUTION_RH12_T14
USR_POWER          = 0x40
USR_POWER_GOOD     = 0x00
USR_POWER_LOW      = USR_POWER
USR_CHIP_HEATER    = 0x02
USR_CHIP_HEATER_ON = USR_CHIP_HEATER   # Consumes 5.5mW, heat by ~1.0°C
USR_CHIP_HEATER_OFF= 0x00
USR_OTP_RELOAD     = 0x01
USR_OTP_RELOAD_ENABLE=0x00
USR_OTP_RELOAD_DISABLE = USR_OTP_RELOAD
USR_DEFAULT = USR_RESOLUTION_DEFAULT | USR_POWER_GOOD | USR_CHIP_HEATER_OFF | USR_OTP_RELOAD_DISABLE

ERR_OK             = 0

DIAG_CIRC_OPEN     = 1
DIAG_CIRC_SHORT    = 2
DIAG_TEMP_OK       = 3
DIAG_HUM_OK        = 4

TEMP_VALID_TIME    = 10  # in seconds
temperature_buf    = 0
timestamp_temp     = 0

def slice_data( data ):
    reading = (data[0] << 8) + (data[1] & 0xFC)
    status = data[1] & 0x03
    check = data[2]
    if status==0:
        if reading==0:
            diag = DIAG_CIRC_OPEN
        else:
            diag = DIAG_TEMP_OK
    else:
        if reading == 0xFFFC:
            diag = DIAG_CIRC_SHORT
        else:
            diag = DIAG_HUM_OK
    return [reading, diag, check]


def get_temperature_now():
    global device_address
    
    data = i2c.read_i2c_block_data(device_address, CMD_GET_TEMP_HOLD, 3 )
    [reading, _, _] = slice_data( data )
    
    # Transfer function: temp = -46,85 + 175,72*reading/2^16
    temp = reading * 175.72 / 0x10000 - 46.85
    # Update buffer
    timestamp_temp = time.time()
    temperature_buf= temp
    return temp

def get_temperature():
    ret = 0
    tNow = time.time()
    if tNow - timestamp_temp > TEMP_VALID_TIME:
        ret = get_temperature_now()
    else:
        ret = temperature_buf
    return ret


def get_measurement():
    global device_address
    
    data = i2c.read_i2c_block_data(device_address, CMD_GET_HUM_HOLD, 3 )
    [reading, _, _] = slice_data( data )

    # RH transfer function: rh = -6 + 125 * reading / 2^16
    hum = reading * 125 / 65536 - 6
    # Now, comnpensate by temperature
    temp = get_temperature()
    hum = hum + (temp - 25) * 0.15
    
    return [hum, temp]


def reset():
    global device_address
    
    ret = ERR_OK
    data = i2c.write_byte( device_address, CMD_RESET )
    time.sleep(1)
    return ret
    
def configure():
    global device_address
    
    ret = ERR_OK
    val = USR_DEFAULT
    val = val & ~USR_RESOLUTION
    val = val | USR_RESOLUTION_RH8_T12
    data = i2c.write_byte_data( device_address, CMD_WRITE_USR_REG, val )
    time.sleep(1)
    return ret

def init():
    ret = ERR_OK
    # Reset sensor
    ret = reset()
    # Configure the sensor
    ret = configure()
    get_temperature_now()
    return ret


def close():
    i2c.close()
    