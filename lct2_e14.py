# -*- coding: utf-8 -*-
import ctypes
from ctypes import cdll, pointer, c_ulong, POINTER
from ctypes import *
import time

class slot(ctypes.Structure):
    _fields_ = [('Base', ctypes.c_ulong),
                ('BaseL', ctypes.c_ulong),
                ('Base1', ctypes.c_ulong),
                ('BaseL1', ctypes.c_ulong),
                ('Mem', ctypes.c_ulong),
                ('MemL', ctypes.c_ulong),
                ('Mem1', ctypes.c_ulong),
                ('MemL1', ctypes.c_ulong),
                ('Irq', ctypes.c_ulong),
                ('BoardType', ctypes.c_ulong),
                ('DSPType', ctypes.c_ulong),
                ('Dma', ctypes.c_ulong),
                ('DmaDac', ctypes.c_ulong),
                ('DTA_REG', ctypes.c_ulong),
                ('IDMA_REG', ctypes.c_ulong),
                ('CMD_REG', ctypes.c_ulong),
                ('IRQ_RST', ctypes.c_ulong),
                ('DTA_ARRAY', ctypes.c_ulong),
                ('RDY_REG', ctypes.c_ulong),
                ('CFG_REG', ctypes.c_ulong)]

class read(ctypes.Structure):
    _fields_ = [('SerNum', ctypes.c_char*9),
                ('BrdName', ctypes.c_char*7),
                ('Rev', ctypes.c_char),
                ('DspType', ctypes.c_char*5),
                ('IsDacPresent', ctypes.c_char),
                ('Quartz', ctypes.c_ulong),
                ('Reserv2', ctypes.c_char*13),
                ('KoefADC', ctypes.c_ushort*8),
                ('KoefDAC', ctypes.c_ushort*4),
                ('Custom', ctypes.c_ushort*32)]

class wadc_par_0(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
                ('s_Type', ctypes.c_ulong),
                ('FIFO', ctypes.c_ulong),
                ('IrqStep', ctypes.c_ulong),
                ('Pages', ctypes.c_ulong),
                
                ('AutoInit', ctypes.c_ulong),
                
                ('dRate', ctypes.c_double),
                ('dKadr', ctypes.c_double),
                ('dScale', ctypes.c_double),
                ('Rate', ctypes.c_ulong),
                ('Kadr', ctypes.c_ulong),
                ('Scale', ctypes.c_ulong),
                ('FPDelay', ctypes.c_ulong),
                
                ('SynchroType', ctypes.c_ulong),
                ('SynchroSensitivity', ctypes.c_ulong),
                ('SynchroMode', ctypes.c_ulong),
                ('AdChannel', ctypes.c_ulong),
                ('AdPorog', ctypes.c_ulong),
                ('NCh', ctypes.c_ulong),
                ('Chn', ctypes.c_ulong * 16),
                ('IrqEna', ctypes.c_ulong),
                ('AdcEna', ctypes.c_ulong)]

#wl = cdll.wlcomp
wl = ctypes.CDLL('lib\\wlcomp.dll')
hDll = ctypes.pointer(c_ulong(wl.LoadAPIDLL('lib\\lcomp.dll')))
hErr = ctypes.pointer(c_ulong())
hIfc = ctypes.pointer(c_ulong(wl.CallCreateInstance(hDll, 0, hErr)))
print 'hDll', hDll.contents.value
print 'hIfc', hIfc.contents.value
print 'hErr', hErr.contents.value

Open = ctypes.pointer(c_ulong(wl.OpenLDevice(hIfc)))
print 'Open', Open.contents.value

Bios = ctypes.pointer(c_ulong(wl.LoadBios(hIfc, 'lib\\E440')))
print 'Bios', Bios.contents.value

Test = ctypes.pointer(c_ulong(wl.PlataTest(hIfc)))
print 'Test', Test.contents.value

sl = ctypes.pointer(slot())
wl.GetSlotParam(hIfc, sl)
print 'Slot', sl.contents.BoardType

pd = ctypes.pointer(read())
print 'ReadPlataDescr', wl.ReadPlataDescr(hIfc, pd)
print 'SerNum', pd.contents.SerNum
print 'BrdName', pd.contents.BrdName
print 'Rev', pd.contents.Rev
print 'DspType', pd.contents.DspType
print 'IsDacPresent', ord(pd.contents.IsDacPresent)
print 'Quartz', pd.contents.Quartz, 'Hz'

L_ADC_PARAM = 1
L_STREAM_ADC = 1
L_POINT_SIZE = 10001

pp = ctypes.pointer(wadc_par_0())

pp.contents.s_Type = L_ADC_PARAM
pp.contents.AutoInit = 1
pp.contents.dRate = 400.0
pp.contents.dKadr = 0.0
pp.contents.dScale = 0.0
pp.contents.SynchroType = 0
pp.contents.SynchroSensitivity = 0
pp.contents.SynchroMode = 0
pp.contents.AdChannel = 0
pp.contents.AdPorog = 0
pp.contents.NCh = 16
pp.contents.Chn[0] = 0
pp.contents.Chn[1] = 1
pp.contents.Chn[2] = 2
pp.contents.Chn[3] = 3
pp.contents.Chn[4] = 4
pp.contents.Chn[5] = 5
pp.contents.Chn[6] = 6
pp.contents.Chn[7] = 7
pp.contents.Chn[8] = 8
pp.contents.Chn[9] = 9
pp.contents.Chn[10] = 10
pp.contents.Chn[11] = 11
pp.contents.Chn[12] = 12
pp.contents.Chn[13] = 13
pp.contents.Chn[14] = 14
pp.contents.Chn[15] = 15
pp.contents.FIFO = 4096
pp.contents.IrqStep = 4096
pp.contents.Pages = 32
pp.contents.IrqEna = 1
pp.contents.AdcEna = 1

Size = ctypes.pointer(ctypes.c_ulong(1000000))
Data = ctypes.pointer(ctypes.c_ushort())
Sync = ctypes.pointer(ctypes.c_ulong())

poi = ctypes.pointer(c_ulong())

print 'RequestBufferStream', wl.RequestBufferStream(hIfc, Size, L_STREAM_ADC)
print 'Allocated memory size(word): ', Size[0]

print 'FillDAQparameters', wl.FillDAQparameters(hIfc, pp, 2)

print '.......... Buffer size(word):      ', Size[0]
print '.......... Pages:                  ', pp.contents.Pages
print '.......... IrqStep:                ', pp.contents.IrqStep
print '.......... FIFO:                   ', pp.contents.FIFO
print '.......... Rate:                   ', pp.contents.dRate
print '.......... Kadr:                   ', pp.contents.dKadr

print 'SetParametersStream', wl.SetParametersStream(hIfc, pp, 2, Size, 
                                                    ctypes.cast(ctypes.pointer(Data), ctypes.POINTER(c_void_p)), 
                                                    ctypes.cast(ctypes.pointer(Sync), ctypes.POINTER(c_void_p)), L_STREAM_ADC)

print '.......... Used buffer size(points):', Size[0]
print '.......... Pages:                   ', pp.contents.Pages
print '.......... IrqStep:                 ', pp.contents.IrqStep
print '.......... FIFO:                    ', pp.contents.FIFO
print '.......... Rate:                    ', pp.contents.dRate
print '.......... Kadr:                    ', pp.contents.dKadr

#print 'GetParameter', wl.GetParameter(hIfc, L_POINT_SIZE, poi)
#print '.......... Point size:', poi[0]

print 'EnableCorrection', wl.EnableCorrection(hIfc, 1)
print 'InitStartDevice', wl.InitStartLDevice(hIfc)
print 'StartDevice', wl.StartLDevice(hIfc)

fr = pp.contents.dRate * 1000   #Hz
tr = 1 / fr                     #s
x1 = []
y = []
x4 = []
y4 = []

N = pp.contents.NCh
k = 0
while k < N:
    i = k
    time.sleep(0.4)
    while i < 131072: 
        if Data[i] < 10000:
            x2 = Data[i]*(10.0/8000)
        elif Data[i] > 10000:
        #else:
            x2 = (Data[i]-65536)*(10.0/8000)
        x1.append(x2)
        y.append(i*tr)
        i += N
    x4.append(x1)
    y4.append(y)
    x1 = []
    y = []
    k += 1

k = 0
while k < N:
    acdc = sum(x4[k]) / (131072 / N)                      # постоянное напряжение
    #acdc = (max(x4[k]) - min(x4[k])) / (1.4142135 * 2)   # переменное напряжение
    acdc = round(acdc, 4)
    print 'Chn', k, acdc
    k += 1

print 'StopDevice', wl.StopLDevice(hIfc)
print 'CloseDevice', wl.CloseLDevice(hIfc)
