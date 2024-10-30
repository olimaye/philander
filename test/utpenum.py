"""
"""
import unittest
from philander.penum import Enum, Flag, auto, unique, idiotypic, dataclass

@unique
@idiotypic
class TestEnum(Enum):
    itemA = auto()
    itemB = auto()
    itemC = auto()
    itemD = auto()
    itemE = auto()
    itemF = auto()
    itemHi = 'Hello'
    itemWorld = 'World'
    
    def check(self):
        return self == TestEnum.itemD
    
@unique
@idiotypic
class TestEnum2(Enum):
    item1 = 1
    item2 = 2
    item3 = 3
    
@idiotypic
class TestFlag(Flag):
    opt0 = auto()
    opt1 = auto()
    opt2 = auto()
    opt3 = auto()
    opt4 = auto()

@dataclass
class TestDataclass:
    attr1 : int = 10
    attr2 : str = "Hello"
    attr3 : float = 4.2
    attr4 : bool = True


class TestPenum( unittest.TestCase ):
    
    def test_enums(self):
        self.assertTrue( len(list(TestEnum)) > 5 )
        i1 = TestEnum.itemA
        self.assertIsNotNone( i1 )
        self.assertEqual( i1, TestEnum.itemA )
        self.assertIs( i1, TestEnum.itemA )
        self.assertIsInstance( i1, TestEnum )

        i2 = TestEnum.itemHi
        self.assertIs( i2, TestEnum.itemHi )
        self.assertIsNot( i2, i1 )
        self.assertNotEqual( i2, i1 )

        i3 = TestEnum.itemC
        # Leave out comparison, here.
        #print( i1<i3, i1<=i3, i1==i3, i1!=i3, i1>=i3, i1>i3)
        self.assertFalse( i3.check() )
        
        for e in TestEnum:
            self.assertIsNotNone( e )
            self.assertIsNotNone( e.value )
            self.assertTrue( e in TestEnum )

        self.assertNotEqual( TestEnum2.item1, TestEnum2.item2 )
        # self.assertEqual( TestEnum2.item1, 1 )
        # self.assertEqual( TestEnum2.item2, 2 )
        # self.assertEqual( TestEnum2.item3, 3 )

    
    def test_flags(self):
        pf = TestFlag.opt0
        self.assertIsNotNone( pf )
        self.assertEqual( pf, TestFlag.opt0 )
        self.assertIs( pf, TestFlag.opt0 )
        self.assertIsInstance( pf, TestFlag )
        pg = TestFlag.opt1
        self.assertIsNotNone( pg )
        self.assertIs( pg, TestFlag.opt1 )

        # Leave out comparison.
        #print( pf<pg, pf<=pg, pf==pg, pf!=pg, pf>=pg, pf>pg)
        # Test binary operators
        self.assertEqual( (pf & pg).value, pf.value & pg.value )
        self.assertEqual( (pf | pg).value, pf.value | pg.value )
        self.assertEqual( (pf ^ pg).value, pf.value ^ pg.value )
        #self.assertEqual( (~pf).value, ~pf.value )
        #self.assertEqual( (~pg).value, ~pg.value )
                
        ph = TestFlag(0x03)
        self.assertIsNotNone( ph )
        self.assertEqual( ph.value, 0x03 )
        for f in TestFlag:
            self.assertIsNotNone( f )
            self.assertIsNotNone( f.value )
            self.assertTrue( f in TestFlag )
    
    def test_dataclass(self):
        dc = TestDataclass()
        self.assertEqual( dc.attr1, 10 )
        self.assertEqual( dc.attr2, "Hello" )
        self.assertEqual( dc.attr3, 4.2 )
        self.assertTrue( dc.attr4 )

        dc = TestDataclass(attr1=17, attr3="World")
        self.assertEqual( dc.attr1, 17 )
        self.assertEqual( dc.attr2, "Hello" )
        self.assertEqual( dc.attr3, "World" )
        self.assertTrue( dc.attr4 )

        self.assertRaises(TypeError, lambda: TestDataclass(1,2,3,4,5,6,7,8,9) )
        self.assertRaises(TypeError, lambda: TestDataclass(attr5="Info") )
        self.assertRaises(TypeError, lambda: TestDataclass(1,2,3,4, attr3="Info") )
        
        
if __name__ == '__main__':
    unittest.main()

