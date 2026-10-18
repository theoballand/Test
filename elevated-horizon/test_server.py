import tempfile, unittest
from pathlib import Path
from server import Store

class Tests(unittest.TestCase):
 def setUp(self):
    self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'test.sqlite3';self.s=Store(self.path)
    self.c=self.s.save('contacts',{'name':'Contact TEST','type':'Agence'})
    self.m={'title':'Mission TEST','contact':self.c['id'],'stage':'Demande','price':'250.00','checks':{}}
 def tearDown(self):self.tmp.cleanup()
 def test_persistence(self):
    self.s.save('missions',self.m);self.assertEqual(Store(self.path).all('missions')[0]['price'],'250.00')
 def test_invalid_price(self):
    for v in ('NaN','-1','1.001','Infinity'):
      with self.assertRaises(ValueError):self.s.save('missions',dict(self.m,price=v))
 def test_quote_snapshot(self):
    m=self.s.save('missions',self.m);q=self.s.save('quotes',{'mission':m['id']});m['price']='300';self.s.save('missions',m)
    self.assertEqual(q['snapshot']['price'],'250.00');self.assertEqual(self.s.all('quotes')[0]['snapshot']['price'],'250.00')
 def test_payment_gate(self):
    with self.assertRaises(ValueError):self.s.save('missions',dict(self.m,stage='Réservation'))
    with self.assertRaises(ValueError):self.s.save('missions',dict(self.m,stage='Livré',deposit=True))
    self.s.save('missions',dict(self.m,stage='Livré',deposit=True,balance=True))
 def test_checks_not_approval(self):
    m=self.s.save('missions',dict(self.m,checks={k:True for k in ('espace','tiers','meteo','assurance','qualification','materiel','acces','identification')}));self.assertEqual(m['stage'],'Demande')
 def test_archive(self):
    self.c['archived']=True;self.s.save('contacts',self.c);self.assertTrue(self.s.all('contacts')[0]['archived'])
if __name__=='__main__':unittest.main()
