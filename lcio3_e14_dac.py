#!/usr/bin/python3-32
# -*- coding: utf-8 -*-
"""Пример работы ЦАП L-CARD E14-440, 440D в асинхронном режиме"""
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

Bios = pointer(c_ulong(wl.LoadBios(hIfc, f'{folder}\\lib\\E440')))
print ('Bios', Bios.contents.value)

Test = pointer(c_ulong(wl.PlataTest(hIfc)))
print ('Test', Test.contents.value)

sl = pointer(Slot())
wl.GetSlotParam(hIfc, sl)
print ('Slot', sl.contents.BoardType)

pd = pointer(Plata())
print ('ReadPlataDescr', wl.ReadPlataDescr(hIfc, pd))
print ('SerNum', pd.contents.SerNum)
print ('BrdName', pd.contents.BrdName)
print ('IsDacPresent', pd.contents.IsDacPresent)
print ('Quartz', pd.contents.Quartz, 'Hz')

L_ASYNC_DAC_OUT = 9

pp = pointer(AsyncParam())
pp.contents.s_Type = L_ASYNC_DAC_OUT
pp.contents.Mode = 0    # 0:1 канал; 1:2 канал

print ('EnableCorrection', wl.EnableCorrection(hIfc, 1))
print ('InitStartDevice', wl.InitStartLDevice(hIfc))
print ('StartDevice', wl.StartLDevice(hIfc))

def setdac(dacval):
    """установка выходного значения ЦАП в мВ"""
    for i in range (100):
        x = (dacval * 2048) / 5000
        pp.contents.Data[0] = int(round(x, 0))
        wl.IoAsync(hIfc, pp)

setdac(1000)

print ('StopDevice', wl.StopLDevice(hIfc))
print ('CloseDevice', wl.CloseLDevice(hIfc))
