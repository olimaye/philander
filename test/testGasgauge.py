from time import sleep
from philander.serialbus import SerialBusDevice
from philander.systypes import ErrorCode
from philander.primitives import Percentage
# Replace this with any other gasgauge to test (conf might need to be adjusted accordingly)
from philander.stc311x import STC311x as Gasgauge
from generalTestSuite import run, MenuFunction


def main():
    # initialize Gasgauge
    gg = Gasgauge()

    # get default settings
    settings = {
            "Gasgauge.pinInt.gpio.pinDesignator": 4  # board 7
            }
    gg.Params_init(settings)

    # set title of test suite
    title = "Test Gasgauge"

    # define available functions
    functions = [
        # connectivity functions
        MenuFunction(gg.open, args=(settings,)),
        MenuFunction(gg.close),
        MenuFunction(gg.reset),
        # data functions
        MenuFunction(gg.getInfo, name="get info"),
        MenuFunction(gg.getStatus, args=(None,), name="get status"),
        MenuFunction(gg.getBatteryVoltage, name="get voltage"),
        MenuFunction(gg.getBatteryCurrent, name="get current"),
        MenuFunction(gg.getBatteryCurrentAvg, name="get current (avg.)"),
        MenuFunction(gg.getRatedSOCStr, name="get SOC-rating"),
        MenuFunction(gg._checkID, name="ID-check",
            custom_output_processor=lambda err: print("ID correct" if err.is_ok() else "ID incorrect")),
        MenuFunction(gg.getChangeRate, name="get change rate"),
        MenuFunction(gg.getBatteryTemperature, name="get battery temperature"),
        MenuFunction(gg.getChipTemperature, name="get chip temperature"),
        ]

    # run test suite
    run(settings, functions, title)

if __name__ == "__main__":
    main()
