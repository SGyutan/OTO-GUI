"""
OTO Photonics

- events and drowing graph at main thread
- Measurment at multithread or multiprocess

ref: https://github.com/PySimpleGUI/PySimpleGUI/blob/master/DemoPrograms/Demo_Matplotlib_Animated.py

"""

import multiprocessing as mp
from threading import Thread
import time

from pathlib import Path
import pandas as pd

# plotlyでhtmlのグラフをSaveするとき
# import plotly.graph_objects as go
# import plotly.io as pio

import datetime

import PySimpleGUI as sg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, FigureCanvasAgg
from matplotlib.figure import Figure
import numpy as np

# import windows_version.PythonDLL_x64.spectraeye_win64_api_ms as spi
import PythonDLL_x64.spectraeye_win64_api_ms as spi
# import keyboard

import warnings
warnings.simplefilter('ignore')

# ui queue : main thread (ui) -> Instruments
# data queue: Instruments -> main thread

ui_que = mp.Queue(1)
data_que = mp.Queue(3)


def draw_figure(canvas, figure, loc=(0, 0)):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg

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

# Measurment Instruments setting
def make_data(ui_que,data_que,para):
   
    spec = spi.SpectraEye()
    # 0.1 seconds = 100000, 100ms = 100,000, 10ms =10,000 
    spec.integT = para[0]
    spec.ave = para[1] 
    msg = para[2]

   
    # print(spec.wavelengths())
    # print(spec.intensities())

    wave = spec.wavelengths()
    ave_ints = np.zeros_like(wave)

    
    while True:
        
        if not ui_que.empty():
            _ = ui_que.get()
            print(f'{now_datetime()}  Abort')
            break
        
        # if keyboard.is_pressed('escape'):
        #     print(f'{now_datetime()}  Abort Escape')
        #     # sys.exit()
            break
        
        if msg == 'RT': #realtime mode
            for i in range(spec.ave):
                ints= spec.intensities(False,False)
                ave_ints =  (ave_ints + ints)/(i+1)
    
            data_que.put([wave,ave_ints])
        
        elif msg == 'D': # measurement mode
            for i in range(spec.ave):
                ints= spec.intensities(False,False)
                ave_ints =  (ave_ints + ints)/(i+1)
                data_que.put([wave,ave_ints])
                
                if not ui_que.empty():
                    flag = ui_que.get()
                    break
            print(f'{now_datetime()}  Finished')
            break
        # time.sleep(0.001)
        
def_font= 'Helvetica 12'   

def main():

    # define the form layout
    layout = [[sg.Text('Reflectance OTO', size=(40, 1),
                justification='center', font='Helvetica 16')],
                [sg.Text('Integration time [ms]', size=(20, 1)),sg.InputText('10',key='-integT-',size=(5,1))],
                [sg.Text('Average times', size=(20, 1)),sg.InputText('50',key='-ave-',size=(5,1))],
                [sg.Text('Sample name', size=(20, 1)),sg.InputText('',key='-sample-')],
                
                [sg.Text('Measurment type',size=(20, 1)), 
                sg.Radio('Realtime', group_id='0', default=True, key='-RT-'),
                sg.Radio('Dark', group_id='0', default=False, key='-DK-'), 
                sg.Radio('Reference', group_id='0', default=False, key='-RF-'),
                sg.Radio('Data', group_id='0', default=False, key='-D-')],
                
                [sg.Button('Start', size=(10, 1),  key='-start-', font=def_font), 
                sg.Button('Abort', size=(10, 1),  key='-abort-', font=def_font),
                sg.Button('Save', size=(10, 1), key='-save-',font=def_font),
                sg.Button('Exit', size=(10, 1), key='-exit-', font=def_font)],
        
                [sg.Canvas(size=(640, 480), key='-CANVAS-')],
                [sg.Output(size=(80, 5))]]

    # to get length of wavelength
    ini_spec = spi.SpectraEye()
    wave_ = ini_spec.wavelengths()
    darkData = np.zeros_like(wave_)
    rfData = np.ones_like(wave_)
    
    del ini_spec
    
    
    window = sg.Window('Reflectance measurment by OTO',
                layout, location=(10, 10), finalize=True)

    canvas_elem = window['-CANVAS-']
    canvas = canvas_elem.TKCanvas

    # draw the initial plot in the window
    fig = Figure()
    ax = fig.add_subplot(111)
    ax.set_xlabel("Intensity")
    ax.set_ylabel("wavelength")
    ax.grid()
    fig_agg = draw_figure(canvas, fig)

    while True:

        event, values = window.read(timeout=10, timeout_key='-timeout-')
        
        if event in ('-exit-', None):
            break
            # exit(69)
        
        elif event == '-start-':
            # ui_que.put(1)
            
            # p = mp.Process(target=make_data,args=(ui_que,data_que))
            # p.start()
            # integtime 100ms = 100,000us
            if values['-RT-'] : 
                integT = int(values['-integT-'])*1000
                ave = int(values['-ave-'])
                msg = 'RT'
                
            elif values['-DK-'] or values['-RF-'] or values['-D-']:
                integT = int(values['-integT-'])*1000
                ave = int(values['-ave-'])
                msg = 'D'
                
            else:
                integT = int(values['-integT-'])*1000
                ave = int(values['-ave-'])
                msg = 'RT'
                
            print(f'{now_datetime()}  Start {msg}')
             
            para = [integT, ave, msg]
            thread = Thread(target=make_data,args=(ui_que,data_que,para), daemon=True).start()

            
        elif event == '-abort-':
            ui_que.put(0)
            
        elif event == '-save-':
            sample = values['-sample-']
            
            if values['-D-']:
                df = pd.DataFrame({'wavelength': rtDx,
                                   'reflectance':rtDy,
                                   'darkdata': darkData,
                                   'reference':rfData,
                                   'reflection':refData})
                filename = f'Ref_{sample}_{now_datetime(type=3)}.csv'
                
            else:
                df = pd.DataFrame({'wavelength': rtDx,'intensity':rtDy})
                filename = f'{sample}_{now_datetime(type=3)}.csv'
            print(f'{now_datetime()}  Save : {filename}') 
            
            Path('./data').mkdir(exist_ok=True)
            save_path = Path('./data/',filename)
            df.to_csv(save_path,index=False)
            filename_fig = f'Ref_{sample}_{now_datetime(type=3)}.png'
            save_path_fig = Path('./data/',filename_fig)
            fig.savefig(save_path_fig)
            
            # Plotly
            # plot = []  # プロットデータを入れるためのlistを作成
            # d = go.Scatter(x=rtDx, y=rtDy, name='Data')  # nameでプロットの凡例を追加
            # plot.append(d)  # プロットデータをlistに追加
            # # グラフのレイアウトをまとめて作成
            # layout = go.Layout(
            #     title=dict(text='data'),  # グラフタイトル
            #     xaxis=dict(title='Wavelenght'),  # 横軸のラベル
            #     yaxis=dict(title='y'),  # 縦軸のラベル
            #     showlegend=True,  # プロットが1本の時は凡例を表示するように指定
            # )
            # # 作成したプロットデータとレイアウトデータをまとめる
            # fig = go.Figure(data=plot, layout=layout)
            # filename_plotly = f'Ref_{sample}_{now_datetime(type=3)}.html'
            # save_path_plotly = Path('./data/',filename_plotly)
            # pio.write_html(fig, f'{str(save_path_plotly)}')
                   
            
        elif event == '-timeout-':
            # realtime drawing 
            if not data_que.empty():
                rtD = data_que.get()                
                rtDx = np.array(rtD[0])
                rtDy = np.array(rtD[1])
                # ylim = (np.min(rtDy),np.max(rtDy))
                ylim = (None,None)
                
                if values['-DK-']:
                    darkData = np.zeros_like(rtDx)
                    # darkData = rtDy.copy()
                    darkData = rtDy
                    # ylim = (np.min(rtDy),np.max(rtDy))
                   
                    
                elif values['-RF-']:
                    rfData = np.zeros_like(rtDx)
                    rfData = rtDy
                    # ylim = (np.min(rtDy),np.max(rtDy))
                    
                    
                elif values['-D-'] :
                    try:
                        refData = rtDy.copy()
                        # ref=(rtDy-darkData)/(rfData-darkData)
                        
                        # To esacape 0 divide
                        A = rtDy-darkData
                        B = rfData-darkData
                        ref = np.divide(A, B, out=np.zeros_like(A), where=B!=0)
                       
                        rtDy = ref         # (248-1948)=> 200-1000nm
                        rtDx = rtDx      # (357-1948)=> 350-1000nm
                        ylim = (np.min(rtDy[357:1948]),np.max(rtDy[357:1948]))
                        
                        
                    # except ZeroDivisionError as e:
                    except :
                        pass
                else:
                    pass
                    
                # print(d)
                ax.cla()                    # clear the subplot
                ax.grid()                   # draw the grid
                ax.plot(rtDx, rtDy, color='Blue',label='Data')
                ax.legend(title=f'Integration Time [ms] : {integT/1000:.0f}\nAverage : {ave}')
                ax.set_ylim(ylim)
                fig_agg.draw()   
                    
        else:
            pass
        
    window.close()

if __name__ == '__main__':
    main()