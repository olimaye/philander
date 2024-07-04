"""A general TestSuite for testing implementations with a simple TUI based menu
"""
__author__ = "Carl Bellgardt"
__version__ = "0.1"
__all__ = ["run", "autoRun", "MenuFunction"]

from simple_term_menu import TerminalMenu
from philander.systypes import ErrorCode 
from time import sleep
import inspect

def _exit():
    exit()

"""Run the generalTestSuite

Opens a TUI menu with a predefined configuration function for editing configuration parameters
and other given functions of the tested implementation.\
An example on how to use this function can be found at the bottom of the file,
and can be executed by running the file directly or as a module.

:param dict settings: Configuration parameters as obtained from the tested implementation's :meth:`Params_init`, possibly.
:param MenuFunction[] functions: Functions to test with given settings and arguments. See :class:`MenuFunction`.
:param string title: Title string for the TUI menu.
:return: None
:rtype: None
"""
def run(settings={}, functions=[], title=""):
    title = ("_" * len(title)) + "\n" + title
    # setup default function
    menu_functions = []
    menu_functions.append( MenuFunction(_config, mode="call-once", name="Edit Config", args=(settings, title)) )
    menu_functions += functions 
    menu_functions.append( MenuFunction(_exit, mode="call-once", name="Exit") )

    # run application
    terminal_menu = TerminalMenu([str(f) for f in menu_functions], title=title)
    while True:
        try:
            sel = terminal_menu.show()
            if sel is None: # sel is None on KeyboardInterrupt
                print("Exited with no Error.")
                break
            menu_functions[sel].run()
        except Exception as e:
            print(f"Exited with Error: {e}")
            break

"""Generate all required arguments for a test and run the generalTestSuite

Retrieves the default configuration parameters from the given implementation class
using its :meth:`Params_init` function. All available class functions of the implementation
will be available in the TUI for testing, using automatic output-processing.
After all required arguments are collected, the test suite will be started (see :meth:`run`).

:param class testClass: The tested implementation class, which must have a :meth:`Params_init`.
:return: None
:rtype: None
"""
""" TODO: WIP
def autoRun(testClass):
    testObject = testClass()
    title = "Test " + type(testClass).__name__
    # get configurable parameters
    params = {}
    testObject.Params_init(params)
    # get available functions
    functions = []
    for func in dir(testClass):
        if callable(getattr(testClass, func)) and not func.startswith('_'):
            f = getattr(testClass, func)
            func_args = inspect.getfullargspec(f)
            kwargs = {}
            runtime_kwargs = {}
            for fa in func_args:
            # TODO: use function data with args and default values
            functions.append(func) # TODO: convert func to Object
"""

def _config(settings, title):
    title += "\n[Config]"
    padding = max([len(str(k)) for k in settings.keys()])
    while True:
        options = [(k, f"{k} {' '*(padding-len(k))}: {v}") for k, v in settings.items()]
        settings_menu = TerminalMenu([o[1] for o in options], title=title)
        try:
            # process selection
            sel = settings_menu.show()
            if sel is None: # sel is None on KeyboardInterrupt
                break
            key, descr = options[sel]
            cur_val = settings[key]
            val_type = type(cur_val)
            print(f"{descr} [{val_type.__name__}]")
            print(f"Old value: {cur_val}")
            # set new value dialogue
            try:
                new_val = input("New value: ")
                if val_type == bool:
                    if new_val.lower() in ["false", "none"]: # non-empty strings will be auto-casted to true, so this custom conversion makes it more intuitive
                        new_val = False
                settings[key] = val_type(new_val)
            except KeyboardInterrupt:
                break
        except Exception as e:
            print(f"Exited with Error: {e}")
            break

def _output_processor(output_processor, output, custom_processor=None):
    # automatic output-processor determination
    if output_processor == "auto":
        if output == None:
            output_processor = None
        elif len(output) == 2:
            if type(output[0]) == ErrorCode:
                if output[0] == ErrorCode.errOk:
                    output_processor = "print-second"
                else:
                    output_processor = "print"
            elif type(output[1]) == ErrorCode:
                if output[1] == ErrorCode.errOk:
                    output_processor = "print-first"
                else:
                    output_processor = "print"
            else:
                output_processor = "print"
        else:
            output_processor = "print"
    if output_processor == "none" or output_processor is None:
        pass 
    # available output-processors [(auto), print, print-first, print-second, custom]
    elif output_processor == "print":
        print(output)
    elif output_processor == "print-first":
        print(output[0])
    elif output_processor == "print-second":
        print(output[1])
    elif output_processor == "custom":
        if custom_processor is not None:
            custom_processor(output)
        else:
            raise AttributeError("output_processor is set to custom but custom_output_processor is None.") 
    else:
        raise AttributeError("Invalid output_processor specified, see docs for reference.")

"""Class for defining functions for the TestSuite to test.

Functions are defined by the underlying implementation function to be called, it's parameters,
and how it's run and it's output is processed.

:param function func: Callable function taken from the tested implementation.
:param string mode:\
    "call-once": call function once and terminate.\
    "call-repeat": call function until terminated through KeyboardInterrupt.
:param string output_processor:\
    "auto": automatically determine method.\
    "none": the method has no output or outputs itself, so no processing is needed.\
    "print": print the output directly.\
    "print-first": the output is a tuple (e.g. with Data and ErrorCode) and the first element should be printed.\
    "print-second": the output is a tuple (e.g. with ErrorCode and Data) and the second element should be printed.\
    "custom": a custom process-function should be called and it's return value is printed. See :param:`custom_output_processor`.\
:param function custom_output_processor: Custom output-process function that is given the implementation's output\
    and should return the processed output as a string. :param:`output_processor` must be set to "custom".
:param string name: The function's display name in the TUI.
:param tuple args: positional arguments the implementation's function needs to run. Will be passed through.
:param dict kwargs: keyword arguments the implementation's function needs to run. Will be passed through.
:param dict(key, Tuple(Input_func, Tuple(args))) runtime_args: keyword arguments with a input function that processes and passes though input when the function is called. "manual input parameters". See :class:`ArgInput`
:return: None
:rtype: None
"""
class MenuFunction:
    def __init__(self, func, mode="call-once", output_processor="auto", custom_output_processor=None, name=None, args=(), kwargs={}, runtime_kwargs={}):
        self.func = func
        self.mode = mode
        self.output_processor = output_processor
        self.custom_output_processor = custom_output_processor
        self.name = name if (name is not None) else func.__name__
        self.args = args
        self.kwargs = kwargs
        self.runtime_kwargs = runtime_kwargs 

    def __repr__(self):
        return self.name

    def run(self):
        # get runtime_args
        rt_args = {}
        for key, input_func_data in self.runtime_kwargs.items():
            print(f"kwarg \"{key}\"")
            rt_args[key] = input_func_data[0](*input_func_data[1]) # TODO: documents this procedure properly or rewrite it
        # run function with set mode
        mode = self.mode
        # call function once
        if mode == "call-once":
            ret = self.func( *self.args, **self.kwargs, **rt_args)
            _output_processor( self.output_processor, ret, self.custom_output_processor )
        # call function repeatedly until KeyboardInterrupt
        elif mode == "call-repeat":
            while True:
                try:
                    ret = self.func( *self.args, **self.kwargs, **rt_args)
                    _output_processor( self.output_processor, ret, self.custom_output_processor )
                    sleep(.2)
                except KeyboardInterrupt:
                    break

"""Collection of ready to use input functions to use for runtime_kwargs (see :meth:`MenuFunction.run`)
"""
class ArgInput:
    """Cast input into a predefined type.

    The function calls the input function and then casts the value to the given data type.

    :param dtype: The data type the input value should be casted to
    :return: Casted input value
    :rtype: dtype (see :param:`dtype`)
    """
    def typeCast(dtype):
        val = input(f"Value [{dtype.__name__}]: ")
        return (dtype)(val) # cast val to dtype
    def unsafeManualType():
        """Evaluate input expression. ONLY USE THIS, IF YOU COMPLETELY UNDERSTAND IT'S DANGERS!

        This function evaluates the input value using pythons buildin evaluate function.
        This is highly vulnerable for code injecting attacks, so try to avoid this.

        :return: Evaluated expression
        :rtype: Unknown
        """
        print("THIS CODE IS UNSAFE AN VULNERABLE FOR CODE INJECTION! Use only for testing.")
        expr = input("Python expression: ")
        return eval(expr)

# example usage of generalTestSuite
if __name__ == "__main__":
    def test_settings(settings):
        print(settings)
        # this function does not return anything, thus the output_processor could be set to "none" (default "auto" will do that)
    
    def test_repeat():
        print("This is a test function, that does nothing but not terminate.")

    def test_args(a): # args can be passed through the args argument
        return f"This input converted into an bool would look like this: a={a}"
        # this function returns something, in this case just the value we want to print. Thud output_processor could be set to "print"
   
    def set_something(val):
        return ErrorCode.errOk, f"Something was set to {val}"
        # this function takes an argument that needs to be set manually every time it is run (e.g. set a digital potentiometer to a new value)

    settings = {"conf": "Test",
                "conf2": 2,
                "config3": False}

    functions = []
    functions.append( MenuFunction(test_settings, args=(settings, )) )
    functions.append( MenuFunction(test_repeat, mode="call-repeat", name="repeat test") )
    functions.append( MenuFunction(test_args, name="args test", args=(42, )) )
    functions.append( MenuFunction(test_args, name="kwargs test", kwargs={'a':43}) )
    functions.append( MenuFunction(set_something, runtime_kwargs={"val": (ArgInput.typeCast, (float,))}))

    title = "Test TestSuite"

    run(settings, functions, title)
