#!/usr/bin/python3-32
# -*- coding: utf-8 -*-
"""Пример работы с АЦП L-CARD E14-440, 440D в потоках"""
import os
import array
from ctypes import CDLL,pointer,POINTER,Structure,cast,c_ulong,c_ushort,c_char,c_double,c_void_p

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

class Adcpar0(Structure):
    """Структура служит для передачи параметров сбора данных в плату"""
    _pack_ = 1 # важно передавать побитно
    _fields_ = [
                ('s_Type', c_ulong),
                ('FIFO', c_ulong),
                ('IrqStep', c_ulong),
                ('Pages', c_ulong),

                ('AutoInit', c_ulong),

                ('dRate', c_double),
                ('dKadr', c_double),
                ('dScale', c_double),
                ('Rate', c_ulong),
                ('Kadr', c_ulong),
                ('Scale', c_ulong),
                ('FPDelay', c_ulong),

                ('SynchroType', c_ulong),
                ('SynchroSensitivity', c_ulong),
                ('SynchroMode', c_ulong),
                ('AdChannel', c_ulong),
                ('AdPorog', c_ulong),
                ('NCh', c_ulong),
                ('Chn', c_ulong * 16),
                ('IrqEna', c_ulong),
                ('AdcEna', c_ulong)]

#wl = cdll.wlcomp
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
print ('Rev', pd.contents.Rev)
print ('DspType', pd.contents.DspType)
print ('IsDacPresent', ord(pd.contents.IsDacPresent))
print ('Quartz', pd.contents.Quartz, 'Hz')

L_ADC_PARAM = 1
L_STREAM_ADC = 1
L_POINT_SIZE = 10001

pp = pointer(Adcpar0())

pp.contents.s_Type = L_ADC_PARAM
pp.contents.AutoInit = 1    # 0-однократный сбор; 1-циклический
pp.contents.dRate = 400.0   # частота опроса каналов в кадре (кГц)
pp.contents.dKadr = 0.0     # интервал между кадрами (мс)
pp.contents.dScale = 0.0
pp.contents.SynchroType = 0
pp.contents.SynchroSensitivity = 0
pp.contents.SynchroMode = 0
pp.contents.AdChannel = 0
pp.contents.AdPorog = 0
pp.contents.NCh = 16        # количество опрашиваемых каналов
pp.contents.FIFO = 4096     # размер половины аппаратного буфера FIFO на плате
pp.contents.IrqStep = 4096  # шаг генерации прерываний
pp.contents.Pages = 32      # размер кольцевого буфера в шагах прерываний
pp.contents.IrqEna = 1      # разрешение генерации прерывания от платы
pp.contents.AdcEna = 1      # разрешение работы АЦП (1/0)

ampl = {10: '0000', 2.5: '0100', 0.625: '1000', 0.1562: '1100'}  # усиление
get_bin = lambda x, n: format(x, 'b').zfill(n)
for p in range(16):
    j = get_bin(p, 4)                             # перебор каналов
    pp.contents.Chn[p] = int(ampl.get(10) + j, 2) # массив с номерами каналов и усилением на них

Size = pointer(c_ulong(1000000))
Data = pointer(c_ushort())
Sync = pointer(c_ulong())

poi = pointer(c_ulong())

print ('RequestBufferStream', wl.RequestBufferStream(hIfc, Size, L_STREAM_ADC))
print ('Allocated memory size(word): ', Size[0])

print ('FillDAQparameters', wl.FillDAQparameters(hIfc, pp, 2))

print ('.......... Buffer size(word):      ', Size[0])
print ('.......... Pages:                  ', pp.contents.Pages)
print ('.......... IrqStep:                ', pp.contents.IrqStep)
print ('.......... FIFO:                   ', pp.contents.FIFO)
print ('.......... Rate:                   ', pp.contents.dRate)
print ('.......... Kadr:                   ', pp.contents.dKadr)

print ('SetParametersStream', wl.SetParametersStream(hIfc, pp, 2, Size,
                                cast(pointer(Data), POINTER(c_void_p)),
                                cast(pointer(Sync), POINTER(c_void_p)), L_STREAM_ADC))

print ('.......... Used buffer size(points):', Size[0])
print ('.......... Pages:                   ', pp.contents.Pages)
print ('.......... IrqStep:                 ', pp.contents.IrqStep)
print ('.......... FIFO:                    ', pp.contents.FIFO)
print ('.......... Rate:                    ', pp.contents.dRate)
print ('.......... Kadr:                    ', pp.contents.dKadr)

print ('GetParameter', wl.GetParameter(hIfc, L_POINT_SIZE, poi))
print ('.......... Point size:', poi[0])

print ('EnableCorrection', wl.EnableCorrection(hIfc, 1))
print ('InitStartDevice', wl.InitStartLDevice(hIfc))
print ('StartDevice', wl.StartLDevice(hIfc))

N = pp.contents.NCh             # кол-во каналов
point = 32768                   # кол-во точек (2048 на канал)
nloop = 10                      # кол-во циклов сбора данных
fr = pp.contents.dRate * 1000   # Hz (для графиков)
tr = 1 / fr                     # s  (для графиков)

def meas(rez, pred):
    """измерения с АЦП"""
    x1 = array.array('f', ())
    y1 = array.array('f', ())
    x2 = [array.array('f', ()) for _ in range(N)]
    y2 = [array.array('f', ()) for _ in range(N)]

    for _ in range(nloop):
        for k in range(N):
            i = k
            while i < point:
                if Data[i] < 10000:
                    data_lc = Data[i] * (pred / 8000)
                else:
                    data_lc = (Data[i] - 65536) * (pred / 8000)
                x1.append(data_lc)
                y1.append(i*tr)
                i += N
            x2[k] = x1
            y2[k] = y1
            x1 = array.array('f', ())
            y1 = array.array('f', ())

    for k in range(N):
        if rez == 'DC':
            data_adc = sum(x2[k]) / (point / N)                      # постоянное напряжение
        elif rez == 'AC':
            data_adc = (max(x2[k]) - min(x2[k])) / (1.4142135 * 2)   # переменное напряжение
        data_adc = round(data_adc, 4)
        print ('Chn', k, data_adc)

meas('DC', 10) # режим (AC или DC) и усиление (10, 2.5, 0.625, 0.1562)

print ('StopDevice', wl.StopLDevice(hIfc))
print ('CloseDevice', wl.CloseLDevice(hIfc))
