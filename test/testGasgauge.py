from time import sleep
from philander.serialbus import SerialBusDevice
from philander.systypes import ErrorCode
from philander.primitives import Percentage
# Replace this with any other gasgauge to test (conf might need to be adjusted accordingly)
from philander.stc311 import STC311 as Gasgauge
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
        MenuFunction(Gasgauge.open, args=(gg, settings)),
        MenuFunction(Gasgauge.close, args=(gg,)),
        MenuFunction(Gasgauge.reset,  args=(gg,)),
        MenuFunction(Gasgauge.getInfo, args=(gg,)),
        MenuFunction(Gasgauge.getStatus, args=(gg,)),
        MenuFunction(Gasgauge.getBatteryCurrent, args=(gg,)),
        MenuFunction(Gasgauge.getBatteryVoltage, args=(gg,)),
        MenuFunction(Gasgauge._checkID, args=(gg,), name="ID-check",
            custom_output_processor=lambda err: print("ID correct" if err == ErrorCode.errOk else "ID incorrect")),
    ]

    # run test suite
    run(settings, functions, title)

if __name__ == "__main__":
    main()
