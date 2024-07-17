from time import sleep
from philander.serialbus import SerialBusDevice
from philander.systypes import ErrorCode
from philander.primitives import Percentage
# Replace this with any other gasgauge to test (conf might need to be adjusted accordingly)
from philander.stc311 import STC3115 as Gasgauge
from generalTestSuite import run, MenuFunction


def main():
    # initialize Gasgauge
    gg = Gasgauge()

    # get default settings
    settings = {}
    gg.Params_init(settings)

    # set title of test suite
    title = "Test Gasgauge"

    # define available functions
    functions = [
        MenuFunction(Gasgauge.open, args=(gg, settings)),
        MenuFunction(Gasgauge.close, args=(gg,)),
        MenuFunction(Gasgauge.reset,  args=(gg,)),
        MenuFunction(gg.getInfo)
    ]

    # run test suite
    run(settings, functions, title)

if __name__ == "__main__":
    main()
