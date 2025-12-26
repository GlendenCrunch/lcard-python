#!/usr/bin/python3-32
# -*- coding: utf-8 -*-
"""Пример работы АЦП L-CARD E14-440, 440D в асинхронном режиме"""
import os
from ctypes import CDLL,pointer,Structure,c_ulong,c_ushort,c_char,c_double

folder = os.getcwd()

class Slot(Structure):
    """Структура описывает параметры виртуального слота"""
    _fields_ = [('Base', c_ulong),
                ('BaseL', c_ulong),
                ('Base1', c_ulong),
                ('BaseL1', c_ulong),
                ('Mem', c_ulong),
                ('MemL', c_ulong),
                ('Mem1', c_ulong),
                ('MemL1', c_ulong),
                ('Irq', c_ulong),
                ('BoardType', c_ulong),
                ('DSPType', c_ulong),
                ('Dma', c_ulong),
                ('DmaDac', c_ulong),
                ('DTA_REG', c_ulong),
                ('IDMA_REG', c_ulong),
                ('CMD_REG', c_ulong),
                ('IRQ_RST', c_ulong),
                ('DTA_ARRAY', c_ulong),
                ('RDY_REG', c_ulong),
                ('CFG_REG', c_ulong)]

class Plata(Structure):
    """Структура описывает FLASH"""
    _fields_ = [('SerNum', c_char*9),
                ('BrdName', c_char*7),
                ('Rev', c_char),
                ('DspType', c_char*5),
                ('IsDacPresent', c_char),
                ('Quartz', c_ulong),
                ('Reserv2', c_char*13),
                ('KoefADC', c_ushort*8),
                ('KoefDAC', c_ushort*4),
                ('Custom', c_ushort*32)]

class AsyncParam(Structure):
    """Cтруктура для передачи параметров асинхронного сбора/выдачи данных при вызове IoAsync"""
    _fields_ = [
                ('s_Type', c_ulong),
                ('FIFO', c_ulong),
                ('IrqStep', c_ulong),
                ('Pages', c_ulong),

                ('dRate', c_double),
                ('Rate', c_ulong),
                ('NCh', c_ulong),
                ('Chn', c_ulong * 128),
                ('Data', c_ulong * 128),
                ('Mode', c_ulong)]

wl = CDLL(f'{folder}\\lib\\wlcomp.dll')
hDll = pointer(c_ulong(wl.LoadAPIDLL(f'{folder}\\lib\\lcomp.dll'.encode('ascii'))))
hErr = pointer(c_ulong())
hIfc = pointer(c_ulong(wl.CallCreateInstance(hDll, 0, hErr)))
print ('hDll', hDll.contents.value)
print ('hIfc', hIfc.contents.value)
print ('hErr', hErr.contents.value)

Open = pointer(c_ulong(wl.OpenLDevice(hIfc)))
print ('Open', Open.contents.value)

Bios = pointer(c_ulong(wl.LoadBios(hIfc, f'{folder}\\lib\\L780')))
print ('Bios', Bios.contents.value)

Test = pointer(c_ulong(wl.PlataTest(hIfc)))
print ('Test', Test.contents.value)

sl = pointer(Slot())
wl.GetSlotParam(hIfc, sl)
print ('Slot', hex(sl.contents.BoardType))

pd = pointer(Plata())
wl.ReadPlataDescr(hIfc, pd)
print ('SerNum', pd.contents.SerNum)
print ('BrdName', pd.contents.BrdName)
print ('Quartz', pd.contents.Quartz, 'Hz')

print ('InitStartDevice', wl.InitStartLDevice(hIfc))
print ('StartDevice', wl.StartLDevice(hIfc))
print ('EnableCorrection', wl.EnableCorrection(hIfc, 1))

L_ASYNC_ADC_INP = 6

pp = pointer(AsyncParam())
pp.contents.s_Type = L_ASYNC_ADC_INP
pp.contents.FIFO = 4096
pp.contents.IrqStep = 4096
pp.contents.Pages = 2
pp.contents.dRate = 100.0
pp.contents.NCh = 1

def meas(chanel, predel):
    for _ in range(10):
        pp.contents.Chn[0] = chanel
        k = wl.IoAsync(hIfc, pp)
        x = pp.contents.Data[0]
        if x < 10000:
            print (k, x*(predel/8000))
        elif x > 10000:
            print (k, (x-65536)*(predel/8000))

print ('-------------10V--------------')
meas(0x00, 10.0) # 10V 0b00000000(0x00)	0b00100000(0x20)
print ('-------------2.5V--------------')
meas(0x40, 2.5) # 2.5V 0b01000000 (0x40) 0b01100000(0x60)
print ('-------------0.625V--------------')
meas(0x80, 0.625) # 0.625V 0b10000000(0x80)	0b01100000(0xA0)
print ('------------0.156V---------------')
meas(0xC0, 0.1562) # 0.156V 0b11000000(0xC0)	0b11100000(0xE0)

print ('StopDevice', wl.StopLDevice(hIfc))
print ('CloseDevice', wl.CloseLDevice(hIfc))
