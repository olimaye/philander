"""
"""
from time import sleep
import unittest

from philander.module import Module
from philander.systypes import ErrorCode

# Globals
gPrefix = "this.specific.prefix."
gParams = {\
    gPrefix + "level.sub.A": 1,
    gPrefix + "level.sub.B": 2,
    gPrefix + "level.div.A": 3,
    gPrefix + "level.div.C": 4,
    gPrefix + "level.div.D": 5,
}

class TestModule( unittest.TestCase ):
    
    #@unittest.skip("Disabled for easier diagnostics.")
    def test_agg_params(self):
        paramsA = gParams.copy()
        paramsB = {\
            "level.sub.B": 10,
            "order.entity.E": 11,
        }
        dRes = Module._aggregateParams( paramsA, paramsB, gPrefix )
        self.assertIn( gPrefix+"level.sub.A", dRes )
        self.assertIn( gPrefix+"level.sub.B", dRes )
        self.assertIn( gPrefix+"level.div.A", dRes )
        self.assertIn( gPrefix+"level.div.C", dRes )
        self.assertIn( gPrefix+"level.div.D", dRes )
        self.assertIn( gPrefix+"order.entity.E", dRes )
        self.assertEqual( dRes[gPrefix+"level.sub.A"], gParams[gPrefix+"level.sub.A"] )
        self.assertEqual( dRes[gPrefix+"level.sub.B"], gParams[gPrefix+"level.sub.B"] )
        self.assertEqual( dRes[gPrefix+"level.div.A"], gParams[gPrefix+"level.div.A"] )
        self.assertEqual( dRes[gPrefix+"level.div.C"], gParams[gPrefix+"level.div.C"] )
        self.assertEqual( dRes[gPrefix+"level.div.D"], gParams[gPrefix+"level.div.D"] )
        self.assertEqual( dRes[gPrefix+"order.entity.E"], paramsB["order.entity.E"] )
        self.assertEqual( len(dRes), len(gParams)+1 )
        
    #@unittest.skip("Disabled for easier diagnostics.")
    def test_ext_params(self):
        paramsA = gParams.copy()
        subPrefix = "level.sub."
        prefix = gPrefix + subPrefix
        dRes = Module._extractParams( paramsA, prefix )
        self.assertIn( "A", dRes )
        self.assertIn( "B", dRes )
        self.assertEqual( dRes["A"], gParams[prefix+"A"] )
        self.assertEqual( dRes["B"], gParams[prefix+"B"] )
        self.assertEqual( len(dRes), 2 )
                
        
if __name__ == '__main__':
    unittest.main()
