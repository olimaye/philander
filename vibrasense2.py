from smbus2 import SMBus, i2c_msg

i2c = SMBus(1)

# Chip address
device_address = 0x4D


ERR_OK             = 0


def get_measurement():
    global device_address
    
    # Read 2 bytes without prior writing of a register number
    msg = i2c_msg.read( device_address, 2 )
    i2c.i2c_rdwr(msg)
    
    if msg.len >= 2:
        data = int.from_bytes( msg, "big" )
    else:
        data = -1

    return data

def init():
    return ERR_OK

def close():
    i2c.close()
