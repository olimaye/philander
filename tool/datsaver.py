"""Saves a large data item as a file.
"""

from philander._bma456_feature import _BMA456_Feature as Feature

def writeDataToFile( data, filename ):
    # Write data
    with open( filename, "wb" ) as f:
        num = f.write( bytearray(data) )
    print("Wrote", num, "/", len(data), " bytes to", filename)
    # Verify
    ident=True
    with open( filename, "rb" ) as f:
        for bd in bytearray(data):
            bf = f.read(1)[0]
            if bf!=bd:
                ident=False
                print("Verification failed at  #", f.tell(), ": ", bf, "<>", bd, sep='' )
                break
    if ident:
        print("Verified successfully.")
    
def main():
    # WEARABLE feature set configuration file
    writeDataToFile( Feature.bma456_wbl_configFile, "bma456_feat_wbl.dat" )
    # HEARABLE feature set configuration file
    writeDataToFile( Feature.bma456_hbl_configFile, "bma456_feat_hbl.dat" )
    # MM (mass market) feature set configuration file
    writeDataToFile( Feature.bma456_mm_configFile, "bma456_feat_mm.dat" )
    # AN (any/no motion) feature set configuration file
    writeDataToFile( Feature.bma456_an_configFile, "bma456_feat_an.dat" )

if __name__ == '__main__':
    main()
