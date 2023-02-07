"""
2023.01.04
OTO spectrometor for Windows 64bit
Python 3
This program and Dll are in the same holder

"""
from pathlib import Path
import datetime

from ctypes import *
from array import *

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Device Initialize
# OTO USB2.0 spectrameter's VID & PID
VID = 1592
PID = 2732

# set dll path
# このファイルがあるパスを取得する
dll_name = "UserApplication.dll"
dllabspath = Path(__file__).resolve().parent / dll_name
# dllabspath = os.path.dirname(os.path.abspath(__file__)) + os.path.sep + dll_name
print(f' dll file path: {dllabspath}')
OTOdll = CDLL(str(dllabspath))

#Check how many device is connected with PC.
intDeviceamout = c_uint64(0)
OTOdll.UAI_SpectrometerGetDeviceAmount.restype = c_uint64
OTOdll.UAI_SpectrometerGetDeviceAmount(VID,PID,byref(intDeviceamout))
print("Device amount:")
print(intDeviceamout.value)

if intDeviceamout.value < 1:
    print("NO device connecting")
    exit()
    
#Open Device
DeviceHandle = c_uint64(0)
OTOdll.UAI_SpectrometerOpen.restype = c_uint64
OTOdll.UAI_SpectrometerOpen(0,byref(DeviceHandle),VID,PID)
print(f"Device handle :{DeviceHandle.value}")
# print(DeviceHandle.value)

#Get Serial number
charSerialnumber = create_string_buffer(16)
OTOdll.UAI_SpectrometerGetSerialNumber(DeviceHandle,byref(charSerialnumber))
print (f"Serial number : {charSerialnumber.value.decode()}")
# print (repr(charSerialnumber.value))
# print (charSerialnumber.value.decode())

#Get Module name
charModulename = create_string_buffer(16)
OTOdll.UAI_SpectrometerGetModelName(DeviceHandle,byref(charModulename))
print (f"Module name : {charModulename.value.decode()}")
# print (repr(charModulename.value))
# print (charModulename.value.decode())

#Get Framesize
intFramesize = c_uint64(0)
OTOdll.UAI_SpectromoduleGetFrameSize.restype = c_uint64
OTOdll.UAI_SpectromoduleGetFrameSize(DeviceHandle,byref(intFramesize))
print(f"Device framesize : {intFramesize.value}")
# print(intFramesize.value)

TempLambda = (c_float*intFramesize.value)()
TempIntensity = (c_float*intFramesize.value)()

#Get wavelength
OTOdll.UAI_SpectrometerWavelengthAcquire(DeviceHandle,byref(TempLambda))
# Lambda = []
# for i in range(0,intFramesize.value):
#     Lambda.append(TempLambda[i])

# Change 'c_float_Array_1128' to 'List' 
Lambda = [TempLambda[i] for i in range(0,intFramesize.value)]

print("finish Initailize")


# Singleton
class Singleton(object):
    def __new__(cls, *args, **kargs):
        if not hasattr(cls, "_instance"):
            cls._instance = super(Singleton, cls).__new__(cls)
        return cls._instance

# class SpectraEye():
class SpectraEye(Singleton):

    def __init__(self, IT=30, avg=2):
        """
    
        Args:
            IT (int, optional): integration time. Defaults to 30.
            avg (int, optional): average. Defaults to 2.
        """
        # Integer = True, max = 10000, min = 1
        self.IT = IT
        # integer = True, max = 100, min = 1
        self.avg = avg

        self.wave = Lambda

    def wavelengths(self):
        
        return self.wave
    
    def intensities(self, correct_dark_counts=True, corerect_nonlinearity=True):
        
        errorcode = OTOdll.UAI_SpectrometerDataOneshot(DeviceHandle,self.IT*1000,byref(TempIntensity),1)
        if(errorcode != 0):
            print("Oneerrorcode = ", errorcode)
            #print(self.IT.get())
            
        if correct_dark_counts:
            #Do Background
            errorcode = OTOdll.UAI_BackgroundRemove(DeviceHandle,self.IT*1000,byref(TempIntensity))
            if(errorcode != 0):
                print("bgerrorcode = ", errorcode)
                
        if corerect_nonlinearity:         
            #Do Linearity
            errorcode =OTOdll.UAI_LinearityCorrection(DeviceHandle,intFramesize,byref(TempIntensity))
            if(errorcode != 0):
                print("lcerrorcode = ", errorcode)
        
        self.ints = [TempIntensity[i] for i in range(0,intFramesize.value)]
        # print(len(self.ints),len(self.wave))

        return self.ints   
        
    def get_data(self,correct_dark_counts=True, corerect_nonlinearity=True):
        
        # global TempLambda
        # global Lambda, DeviceHandle
        # global TempIntensity
        # global intFramesize  
        

        errorcode = OTOdll.UAI_SpectrometerDataAcquire(DeviceHandle,self.IT*1000,byref(TempIntensity),self.avg)
        # errorcode = OTOdll.UAI_SpectrometerDataOneshot(DeviceHandle,self.IT*1000,byref(TempIntensity),self.avg)
        
        if(errorcode != 0):
            print("Oneerrorcode = ", errorcode)
            #print(self.IT.get())
            
        if correct_dark_counts:
            #Do Background
            errorcode = OTOdll.UAI_BackgroundRemove(DeviceHandle,self.IT*1000,byref(TempIntensity))
            if(errorcode != 0):
                print("bgerrorcode = ", errorcode)
                
        if corerect_nonlinearity:       
            #Do Linearity
            errorcode =OTOdll.UAI_LinearityCorrection(DeviceHandle,intFramesize,byref(TempIntensity))
            if(errorcode != 0):
                print("lcerrorcode = ", errorcode)
        
        # Do Absolute Intensity Calibration. for Color measurement only.
        # errorcode = OTOdll.UAI_AbsoluteIntensityCorrection(DeviceHandle, byref(TempIntensity), self.IT*1000)
        # if(errorcode != 0):
        #     print("aberrorcode = ", errorcode)
        
        self.ints = [TempIntensity[i] for i in range(0,intFramesize.value)]
        # print(len(self.ints),len(self.wave))

        return self.wave, self.ints

    def graph(self,x=None,y=None):
        
        if x is None:
            x = self.wave
        if y is None:
            y= self.ints
            
        plt.clf()
        plt.plot(np.array(x), np.array(y))
        plt.title ("Spectrum")
        plt.ylabel("Absolute Count(uW/cm^2/nm)")
        plt.xlabel("Lambda(nm)")
        plt.ylim(ymin=0)
        plt.draw()
        plt.pause(1) # sec
        # plt.show()
        # plt.savefig(f'oto_{now_datetime(3)}.png')
        
    def dataframe(self):
        self.df = pd.DataFrame({'wave':self.wave,
                            'intensity':self.ints})
        return self.df
        
    def save_csv(self,filename):
        """
        filename:
        example  'data/dst/to_csv_out.csv'
        """
        self.df_ = self.dataframe()
        self.df_.to_csv(filename,index=False)
           
    def close(self):

        errorcode = OTOdll.DLI_SpectrometerClose(DeviceHandle)
        if(errorcode == 0):
            print("close!!")


def now_datetime(type=1):
    """
    Return the date and time as a string
    
    params:
        type1:default "%Y-%m-%d %H:%M:%S"
        type2:"%Y%m%d%H%M%S"
        type3:"%Y%m%d_%H%M%S"
        type4:"%Y%m%d%H%M"
        elae: Only date "%Y%m%d"

    return
        str: the date and time
    """
    now = datetime.datetime.now()
    if type == 1:
        now_string = now.strftime("%Y-%m-%d %H:%M:%S")
    elif type == 2:
        now_string = now.strftime("%Y%m%d%H%M%S")
    elif type == 3:
        now_string = now.strftime("%Y%m%d_%H%M%S")
    elif type == 4:
        now_string = now.strftime("%Y%m%d%H%M")
    elif type == 5:
        now_string = now.strftime("%m%d_%H:%M:%S")
    elif type == 6:
        now_string = now.strftime("%Y%m%d")    
    else:
        now_string = now

    return  now_string
        

if __name__ == '__main__':
    import time
    
    test = SpectraEye(IT=30, avg=10)
    test.get_data()
    test.graph()
    # time.sleep(0.1)
    # test = SpectraEye(IT=30, avg=50)
    # test.get_data()
    # test.graph()
    # time.sleep(0.1)
    # test = SpectraEye(IT=100, avg=10)
    # test.get_data()
    # test.graph()
    # plt.plot(w,Int)
    # plt.show()
    print(test.wavelengths())
    print(test.intensities(False,False))



# def plot_graph_b64(xdata, ydata):
#     """
#     BytesIOでメモリに保存して、base64でエンコードしたものを返します。
#     :param
#     :return:
#     """
#     plt.clf()
#     plt.plot(xdata, ydata)
#     plt.title("Spectrum")
#     plt.ylabel("Absolute Count(uW/cm^2/nm)")
#     plt.xlabel("Lambda(nm)")
#     # plt.show()
#     buf = BytesIO()
#     plt.savefig(buf, format="png")

#     fig_b64str = base64.b64encode(buf.getvalue()).decode("utf-8")
#     fig_b64data = "data:image/png;base64,{}".format(fig_b64str)

#     return fig_b64data

# ref_file = 'ref_Al.csv'
# def read_ref_file(ref_file) :
#     """
#     read measurment parameater IT, ave, box from referrence file
#     Parameters
#     ----------
#     ref_file

#     Returns
#     -------

#     """
#     with open(ref_file, 'r') as f:
#         for i in range(8):
#             st = f.readline()
#             if 'integration time :' in st:
#                 IT = int(st[18:])
#                 # print(IT)
#             if 'Average :' in st:
#                 avg = int(st[9:])
#                 # print(avg)
#             if 'boxcar :' in st:
#                 box = int(st[8:])
#                 # print(box)

#     ref = np.loadtxt(ref_file, delimiter=',', skiprows=13)
#     # ref is numpy array, select intensity colum
#     # print(ref,type(ref))
#     ref_intensity = ref[:, 1]
#     # ref_wave = ref[:,0]
#     # print(np.shape(ref_wave))
#     return IT, avg, box, ref_intensity
