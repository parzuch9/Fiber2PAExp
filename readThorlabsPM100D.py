import visa
import pyvisa
from ThorlabsPM100 import ThorlabsPM100
import time
#http://132.163.53.187:56000/
rm = pyvisa.ResourceManager()
res = rm.list_resources()
#address = [s for s in res if 'USB0::0x1313::0x8078::P0025639::INSTR' in s]
#print((res))

#inst = rm.get_instrument(address[0])
#pm = ThorlabsPM100(inst = inst)

inst = rm.open_resource('USB0::0x1313::0x8078::P0025639::INSTR')#, term_chars='\\n', timeout=1)
pm = ThorlabsPM100.ThorlabsPM100(inst = inst)
print('Connected to {}'.format(pm))

pm.configure.scalar.power()
pm.sense.correction.wavelength = 810
pm.sense.average.count=20

def get_power():
   return(pm.read)

# tic = time.perf_counter()
# print(pm.read)
# toc = time.perf_counter()
# print(toc-tic)