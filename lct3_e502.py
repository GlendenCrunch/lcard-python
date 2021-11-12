#!/usr/bin/python3-32
# -*- coding: utf-8 -*-
import ctypes
from ctypes import cdll, pointer, c_ulong, Structure
import time
import math
import array

# ------------------------------ Structure e502 -------------------------------------
class Read_x502(Structure):
    _pack_ = 1
    _fields_ = [('arr', ctypes.c_uint32 * 1),   # 1 список, т.к. одна плата
                ('devs', ctypes.c_uint32)]

class t_x502_cbr_coef(Structure):
    _pack_ = 1
    _fields_ = [('offs', ctypes.c_double),
                ('k', ctypes.c_double)]

class t_x502_cbr(Structure):
    _pack_ = 1
    _fields_ = [('adc', t_x502_cbr_coef*6),
                ('rez1', ctypes.c_uint32*64),
                ('dac', t_x502_cbr_coef*2),
                ('rez2', ctypes.c_uint32*20)]

class t_x502_info(Structure):
    _pack_ = 1
    _fields_ = [('BrdName', ctypes.c_char*32),
                ('SerNum', ctypes.c_char*32),
                ('devflags', ctypes.c_uint32),
                ('fpga_ver', ctypes.c_uint16),
                ('plda_ver', ctypes.c_uint8),
                ('board_rev', ctypes.c_uint8),
                ('mcu_firmware_ver', ctypes.c_uint32),
                ('factory_mac', ctypes.c_uint8*6),
                ('rezerv', ctypes.c_uint8*110),
                ('cbr', t_x502_cbr)]
# --------------------------------------------------------------------------------
pp = ctypes.pointer(Read_x502())
pp2 = ctypes.pointer(t_x502_info())
#pp3 = ctypes.pointer(t_x502_cbr())
#pp4 = ctypes.pointer(t_x502_cbr_coef())

lib = cdll.LoadLibrary('lib\\e502api.dll')
lib2 = cdll.LoadLibrary('lib\\x502api.dll')

#UsbGet = lib.E502_UsbGetSerialList(pp.contents.arr, 2, 0, pp.contents.devs)
#UsbGet = lib.E502_UsbGetDevRecordsList(pp.contents.arr, 2, 0, pp.contents.devs)
#print ('UsbGet:', UsbGet)
#print ('devs:', pp.contents.devs)
#print ('arr:', pp.contents.arr[0])  # нулевой индекс, т.к. одна плата

Create = lib2.X502_Create()
print ('Create:', Create)

#Open = lib.X502_OpenByDevRecord(Create, 0)
Open = lib.E502_OpenUsb(Create, 0)  # 0 - конект к первой подключенной плате
print ('Open:', Open)

Info = lib2.X502_GetDevInfo(Create, pp2)
print ('Info:', Info)
print ('BrdName:', pp2.contents.BrdName)
print ('SerNum:', pp2.contents.SerNum)
print ('devflags:', pp2.contents.devflags)
print ('fpga_ver:', pp2.contents.fpga_ver)
print ('plda_ver:', pp2.contents.plda_ver)
print ('board_rev:', pp2.contents.board_rev)
print ('mcu_firmware_ver:', pp2.contents.mcu_firmware_ver)
#print ('factory_mac:', pp2.contents.factory_mac)
#print ('rezerv:', pp2.contents.rezerv)
#print ('cbr:', pp2.contents.cbr)

for i in range(6):
    print ('-->ADC cbr_offs {}: {}'.format(i, pp2.contents.cbr.adc[i].offs))
    print ('-->ADC cbr_koef {}: {}'.format(i, pp2.contents.cbr.adc[i].k))

for i in range(2):
    print ('-->DAC cbr_offs {}: {}'.format(i, pp2.contents.cbr.dac[i].offs))
    print ('-->DAC cbr_koef {}: {}'.format(i, pp2.contents.cbr.dac[i].k))
    coef_dac_list.append(pp2.contents.cbr.dac[i].offs)
    coef_dac_list.append(pp2.contents.cbr.dac[i].k)

lib2.X502_SetSyncMode (Create, 0)
lib2.X502_SetRefFreq(Create, 2000000)

# ========================= DAC ==========================================
#volt_dac = [3000]                  # DC mV
volt_dac = array.array('f', ())     # AC
Um = 2000                           # rms mV
f = 10000                           # Hz
size = 1000000
dac_numb =  0x10
for x in range(size):
    y_sin_analog = (Um * (math.sin(x * 2 * math.pi * f / size))) * math.sqrt(2) * (30000 / 5000)
    volt_dac.append(y_sin_analog)
# ========================================================================
def dac_synchr():
    # Работа с модулем при синхронном потоковом выводе на ЦАП:
    pyarr = (ctypes.c_double * len(volt_dac))(*volt_dac)            # начальный массив с некалиброванными значениями
    volt_dac_ok = (ctypes.c_double * len(volt_dac))()               # возвращаемый массив с калиброванными значениями
    #lib2.X502_AsyncOutDac(Create, 1, int(volt_dac[0]), 0x0002)

    lib2.X502_SetOutFreq(Create, ctypes.pointer(ctypes.c_double(size)))
    lib2.X502_StreamsEnable(Create, dac_numb)
    lib2.X502_PreloadStart(Create)
   
    for i in range(500):
        lib2.X502_PrepareData(Create, pyarr, pyarr, 'NULL', size, 0x0002, volt_dac_ok)
        lib2.X502_Send(Create, volt_dac_ok, size, 10)
        lib2.X502_Configure(Create, 0)
        lib2.X502_StreamsStart(Create)

def close():
    lib2.X502_StreamsStop(Create)
    lib2.X502_Close(Create)
    lib2.X502_Free(Create)

if __name__ == '__main__':
    dac_synchr()
    #dac_cycle()
    close()
