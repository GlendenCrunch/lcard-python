#!/usr/bin/python3-32
# -*- coding: utf-8 -*-
import math
import array
import time
import ctypes
import usb1
from struct import pack, unpack
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure, show
import numpy as np
from numpy import mean, sqrt, square
import os

# ============= Запись в регистр FPGA ================
# 0xC0 - приеме из модуля
# 0x40 - передача данных в модуль
# ====================================================
# 0x10 - чтение значения регистра ПЛИС
# 0x11 - Запись значения регистра ПЛИС
# ====================================================
# 0x06 - Получение текущего скоростного режима работы интерфейса USB (0 — Full Speed, 1 — High Speed)
# 0x12 - Запуск обмена потоковыми данными
# 0x13 - Останов обмена потоковыми данными
# 0x14 - Установка шага передачи данных
# 0x15 - Проверка, запущена ли обмен потоковыми данными (0 — нет, 1 — запущена)
# 0x17 - Чтение блока данных из Flash-памяти модуля
# 0x18 - Запись блока данных во Flash-память модуля
# 0x19 - Стирание блока данных во Flash-памяти модуля
# 0x1A - Изменение уровня защиты Flash-памяти модуля
# ====================================================

lib = ctypes.cdll.LoadLibrary('lib\\e502api.dll')
lib2 = ctypes.cdll.LoadLibrary('lib\\x502api.dll')
Create = lib2.X502_Create()
Open = lib.E502_OpenUsb(Create, 0)
lib2.X502_Close(Create)

def first_load():
    global handle
    global context
    context = usb1.USBContext()
    handle = context.openByVendorIDAndProductID(0x2A52,0xE502)
    handle.claimInterface(0)

    #led_on_of = handle.controlWrite(0x40, 0x11, 0x200+0x114, 0, pack( "I", 1))     # 1 - горит led, 0 - не горит
    #usb_speed = handle.controlRead(0xC0, 0x06, 0, 0, 1)                            # Скорость USB
    #print('Скорость USB: ' + str(int.from_bytes(usb_speed, "big", signed=False)))

    b = handle.controlRead(0xC0, 0x80, 0, 0, 80)                                    # Чтение информации о модуле
    #print(b)
    c = b.decode('UTF-8')
    print('Тип: ' + c[0:4])
    print('Зав. №: ' + c[32:40])

    #flash = handle.controlRead(0xC0, 0x17, 0x1F0000, 0, 512)
    #print('Flash:', flash)

def close():
    context.close()

def adc_low():
    # ========================= ADC ==========================================
    number_ch = 15                                  # кол-во логичеcких каналов каналов + 1
    Amp = 0                                         # усиление (0:10V; 1:5V; 2:2V; 3:1V; 4:0,5V; 5:0,2V)
    Amp_del = 10
    dRate = 0                                       # делитель частоты (2MHz / (dRate + 1))
    point = 8192*(number_ch + 1)*(16 - number_ch)   # кол-во точек в буфере на канал 8192
    size_data_bulk = (4 * (number_ch + 1)) * 8      # 512 - размер данных по usb
    # ========================================================================
    data_ch_writ = handle.controlWrite(0x40, 0x11, 0x200+0x100, 0, pack( "I", number_ch))
    #data_ch_read = handle.controlRead(0xC0, 0x10, 0x200+0x100, 0, 1)
    #print('Каналов: ' + str(bin(data_ch_read[0])[2:]))

    j = 8 * number_ch + Amp
    for i in range(number_ch + 1):
        data_table_writ = handle.controlWrite(0x40, 0x11, 512 + i, 0, pack( "I", j))        # Таблица настроек логических каналов
        j -= 8

    #data_table_read = handle.controlRead(0xC0, 0x10, 0x200+0x0, 0, 4)
    #print(data_table_read)
    #print('Таблица: ' + str(bin(data_table_read[0])[2:].zfill(8)) + str(bin(data_table_read[1])[2:].zfill(8)))

    data_freq1_writ = handle.controlWrite(0x40, 0x11, 0x200+0x102, 0, pack("I", dRate))    # Делитель O_HARD
    #data_freq1_read = handle.controlRead(0xC0, 0x10, 0x200+0x102, 0, 1)
    #print('Делитель частоты АЦП O_HARD: ' + str(int.from_bytes(data_freq1_read, "big", signed=False)))
    data_freq2_writ = handle.controlWrite(0x40, 0x11, 0x400+0x12, 0, pack( "I", dRate))     # Делитель IO_ARITH

    data_1_0 = handle.controlWrite(0x40, 0x12, 0, 0, pack( "I", 1))                     # запуск потока на ввод
    #data_1_1 = handle.controlRead(0xC0, 0x15, 0, 0, 10)                                # проверка запуска потока
    #print('Статус потока: ' + str(int.from_bytes(data_1_1, "big", signed=False)))

    # Регистр IN_STREAM_ENABLE: Разрешение синхронных потоков на ввод
    data_synch_writ = handle.controlWrite(0x40, 0x11, 0x400+0x19, 0, pack( "I", 1))     # (бит 0 разрешает ввод с АЦП, бит 1 — с цифровых линий)

    data_preload_adc = handle.controlWrite(0x40, 0x11, 0x200+0x10C, 0, pack( "I", 1))   # запись 1 в регистр 0x10C
    data_preload_adc = handle.controlWrite(0x40, 0x11, 0x200+0x10C, 0, pack( "I", 1))   # запись 1 в регистр 0x10C
    data_syn_wrt = handle.controlWrite(0x40, 0x11, 0x200+0x10A, 0, pack( "I", 1))       # запуск синхронного ввода-вывода

    fr = 2E+6
    tr = 1 / fr

    def two2dec(s):                                         # перевод из двоичной в десятичную с учетом знака
        if s[0] == '1':
            return -1 * (int(''.join('1' if x == '0' else '0' for x in s), 2) + 1)
        else:
            return int(s, 2)

    def smooth(y, box_pts):                                 # функция сглаживания
        box = np.ones(box_pts) / box_pts
        y_smooth = np.convolve(y, box, mode='same')
        return y_smooth

    for d in range(1):
        buff = array.array('f', ())                             # общий буффер
        while len(buff) != point:                               # заполняем буффер до point
            data_read = handle.bulkRead(0x1, size_data_bulk)    # чтение данных  по usb
            #print(len(data_read))
            #print(data_read)
            j = 0
            while j < len(data_read):
                x0 = bin(data_read[j])[2:].zfill(8)
                x1 = bin(data_read[j + 1])[2:].zfill(8)
                x2 = bin(data_read[j + 2])[2:].zfill(8)
                x3 = data_read[j + 3] - 192
                #samples = two2dec(x2 + x1 + x0)
                data_lc = ((two2dec(x2 + x1 + x0) / 6000000) * Amp_del)
                #accu =  ((data_lc - (1)) / 10) * 100
                buff.append(data_lc)
                #print('Volt ch_{}: {}, accur: {}'.format(x3, data_lc, accu))
                #print(samples)
                j += 4

        y = array.array('f', ())
        y4 = [array.array('f', ()) for _ in range(number_ch + 1)]
        x5 = array.array('f', ())
        x6 = [array.array('f', ()) for _ in range(number_ch + 1)]
        for k in range(number_ch + 1):
            j = k
            while j < point:          
                x5.append(buff[j])
                y.append(j*tr)
                #print(j)
                j += number_ch + 1
            x6[k] = smooth(x5, 1)
            y4[k] = y
            x5 = array.array('f', ())
            y = array.array('f', ())

        for k in range(number_ch + 1):            
            #acdc = sum(x6[k]) / (point / (number_ch + 1))                        # dc
            acdc = math.sqrt(sum(i*i for i in x6[k][819:]) / len(x6[k][819:]))    # rms
            #acdc = sqrt(mean(square(x6[k])))                                     # numpy rms
            data_accur = ((acdc - 8) / 8) * 100
            print ('Chn', k, acdc * 1000, 'accur', data_accur)

    data_syn_wrt = handle.controlWrite(0x40, 0x11, 0x200+0x10A, 0, pack( "I", 0)) # остановка синхронного ввода-вывода
    data_2_0 = handle.controlWrite(0x40, 0x13, 0, 0, pack( "I", 1))               # остановка потока на ввод
    #data_2_1 = handle.controlRead(0xC0, 0x15, 0, 0, 10)                          # проверка запуска потока
    #print('Статус потока: ' + str(int.from_bytes(data_2_1, "big", signed=False)))
    #print(buff)
    #print(len(buff))

def adc_graph():
    fig = figure(1)
    ax1 = fig.add_subplot(211)
    ax1.plot(y4[2], x6[2])
    ax1.grid(True)
    ax1.set_xlim((0, 0.5))
    ax1.set_ylabel('U, V')
    l1=ax1.set_title('t, sec')
    l1.set_color('g')
    l1.set_fontsize('large')
    show()

first_load()
adc_low()
close()
