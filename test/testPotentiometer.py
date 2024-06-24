from time import sleep
from philander.serialbus import SerialBusDevice
from philander.systypes import ErrorCode

# Replace this with any other potentiometer to test (conf might need to be adjusted accordingly)
from philander.mcp40d import MCP40D as potentiometer
from philander.potentiometer import Potentiometer

WAIT_BETWEEN_SET_GET = .5
WAIT_BETWEEN_NEXT_TEST = 2.5

def main():
    conf = {
        "SerialBus.designator": "/dev/i2c-1",
        "SerialBusDevice.address": 0x2E,
        "Potentiometer.resistance.max": 100000,
        "Potentiometer.resolution": 128
        }
    pot_steps = 2 ** conf["Potentiometer.resolution"]
    err_counter = 0
    
    poti = potentiometer()
    poti.open(conf)
    
    # test percentage values from 0 to 100 in steps of 10
    for i in range(0, 110, 10):
        err = poti.set(i)
        if err != ErrorCode.errOk:
            print(f"Error while set(): {err}")
            err_counter += 1
        print(f"Potentiometer set to {i}%.")
        sleep(WAIT_BETWEEN_SET_GET)

        # test values
        data, err = poti.get(asDigital=True)
        if err != ErrorCode.errOk:
            print(f"Error while get(): {err}")
            err_counter += 1
        expected_val = poti._digitalize_resistance_value(percentage=i) # TODO: do with actual percentage value
        actual_val = data
        expected_val_percent = i
        actual_val_percent = (data * 100) / (pot_steps - 1)
        
        if actual_val == expected_val:
            print(f"Read value is correct.")
        else:
            print(f"VALUE NOT CORRECT: Potentiometer resistance value should be {expected_val} ({round(expected_val_percent, 1)}%) but is set to {actual_val} ({round(actual_val_percent, 1)}%)")
        sleep(WAIT_BETWEEN_NEXT_TEST)
    
    # test resistance values from 0 to <max> in steps of 10% * <max>
    for n in range(0, 110, 10):
        i = (n/100) * conf["Potentiometer.resistance.max"]
        err = poti.set(i, isAbsolute=True)
        if err != ErrorCode.errOk:
            print(f"Error while set(): {err}")
            err_counter += 1
        print(f"Potentiometer set to {i} Ohms.")
        sleep(WAIT_BETWEEN_SET_GET)
        
        # test values
        data, err = poti.get(asDigital=True)
        if err != ErrorCode.errOk:
            print(f"Error while get(): {err}")
            err_counter += 1
        expected_val = poti._digitalize_resistance_value(absolute=i)
        actual_val = data
        expected_val_ohms = i
        actual_val_ohms = data * (conf['Potentiometer.resistance.max'] / pot_steps)
        
        if actual_val == expected_val:
            print(f"Read value is correct.")
        else:
            print(f"VALUE NOT CORRECT: Potentiometer resistance value should be {expected_val} ({round(actual_val_ohms)} ohms) but is set to {actual_val} ({round(actual_val_ohms)} ohms)")
        sleep(WAIT_BETWEEN_NEXT_TEST)

    print("Closing connection.")
    poti.close()
    print(f"Test finished with {err_counter} errors caught.")


if __name__ == "__main__":
    main()
