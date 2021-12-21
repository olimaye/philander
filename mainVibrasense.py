import vibrasense

#
# Main program
#

vibrasense.init()

try:
    print("Measurement started. Press Ctrl+C to end.")
    while True:
       continue
    
except KeyboardInterrupt:
    pass

vibrasense.close()
print("OK.")
