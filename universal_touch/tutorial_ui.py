"""Interactive native onboarding. All practice input stays inside this window."""
import time
import tkinter as tk
from tkinter import ttk

from .precise_control import PreciseController
from .tutorial import TrainingMouse, TutorialProgress


class Tutorial:
    def __init__(self,parent,camera_index,on_close,fps=15,mirror=True,gain=1.8):
        self.on_close = on_close
        self.camera_index = camera_index
        self.fps,self.mirror = fps,mirror
        self.camera = self.tracker = None
        self.running = self.closed = False
        self.job = None
        self.last_preview = 0.
        self.progress = TutorialProgress()
        self.mouse = TrainingMouse()
        self.controller = PreciseController(self.mouse,mirror=mirror,gain=gain)
        self.window = tk.Toplevel(parent)
        self.window.title('UniversalTouch · aprender com a mão')
        self.window.geometry('590x660')
        self.window.minsize(560,650)
        self.window.configure(bg='#101820')
        self.window.transient(parent)
        self.window.protocol('WM_DELETE_WINDOW',lambda:self.close(False))
        self.window.bind('<Escape>',lambda _:self.pause())
        body = ttk.Frame(self.window,padding=20)
        body.pack(fill='both',expand=True)
        ttk.Label(body,text='Vamos praticar primeiro',style='Title.TLabel').pack(anchor='w')
        self.heading = tk.StringVar(value='1 de 3 · levante só o indicador')
        self.instruction = tk.StringVar(value='Fique de frente para a webcam, com boa luz. Levante só o indicador, com a palma para a câmera e os outros dedos dobrados sem apertar. Afaste o polegar do indicador.')
        self.status = tk.StringVar(value='A câmera só liga ao clicar em Começar treino.')
        ttk.Label(body,textvariable=self.heading,font=('sans',13,'bold')).pack(anchor='w',pady=(12,6))
        ttk.Label(body,textvariable=self.instruction,wraplength=540).pack(anchor='w')
        self.canvas = tk.Canvas(body,width=520,height=205,bg='#182632',highlightthickness=0)
        self.canvas.pack(fill='x',pady=(14,10))
        row = ttk.Frame(body)
        row.pack(fill='x')
        self.preview_label = ttk.Label(row,text='Sua câmera aparecerá aqui',width=24,anchor='center')
        self.preview_label.pack(side='left',padx=(0,12))
        ttk.Label(row,text='O ponto verde é o seu cursor de treino.\n\nDurante o tutorial, gestos não clicam\nem outros programas.',wraplength=300,justify='left').pack(side='left',anchor='n')
        ttk.Label(body,textvariable=self.status,wraplength=540,foreground='#65e5d3').pack(anchor='w',pady=12)
        self.start_button = ttk.Button(body,text='Começar treino · ligar câmera',command=self.toggle)
        self.start_button.pack(fill='x')
        self.finish_button = ttk.Button(body,text='Concluir e usar UniversalTouch',state='disabled',command=lambda:self.close(True))
        self.finish_button.pack(fill='x',pady=(8,3))
        ttk.Button(body,text='Pular por enquanto',command=lambda:self.close(True)).pack(anchor='e')
        self.draw(None)
        self.window.update_idletasks()
        self.window.grab_set()
        self.window.lift()
        self.window.focus_set()

    def toggle(self):
        if self.running: self.pause()
        else: self.start()

    def start(self):
        if self.closed or self.progress.done: return
        self.status.set('Preparando a câmera…')
        self.window.update_idletasks()
        try:
            from .vision import HandTracker, Camera
            self.tracker = HandTracker()
            self.camera = Camera(self.camera_index)
            self.controller.set_paused(False)
            self.running = True
            self.start_button.configure(text='Pausar treino · desligar câmera')
            self.tick()
        except Exception as exc:
            self.pause()
            self.status.set(str(exc))

    def pause(self):
        self.running = False
        if self.job is not None:
            self.window.after_cancel(self.job)
            self.job = None
        self.controller.close()
        if self.camera: self.camera.close()
        self.camera = self.tracker = None
        self.start_button.configure(text='Retomar treino · ligar câmera')
        self.preview_label.configure(image='',text='Câmera desligada')
        self.preview_label.image = None
        self.status.set('Treino pausado · câmera desligada')

    def tick(self):
        self.job = None
        if not self.running or self.closed: return
        started = time.monotonic()
        try:
            frame = self.camera.latest()
            if frame is not None:
                kp = self.tracker(frame)
                result = self.controller.update(kp,frame.shape,started)
                self.progress.update(result.pointer,self.controller.armed,self.mouse.presses,kp is not None)
                self.draw(result.pointer,result.progress)
                if started-self.last_preview > .33:
                    self.preview(frame,kp)
                    self.last_preview = started
                self.status.set(result.status)
                self.update_instructions()
                if self.progress.done:
                    self.pause()
                    self.status.set('Treino concluído · agora você pode usar os gestos no PC.')
                    self.finish_button.configure(state='normal')
                    self.start_button.configure(state='disabled')
                    return
            elif started-self.camera.last_frame > 2.:
                raise RuntimeError('A câmera não entregou imagens. Feche outros aplicativos de câmera e tente de novo.')
        except Exception as exc:
            self.pause()
            self.status.set(str(exc))
            return
        self.job = self.window.after(max(1,round(1000*(1/self.fps-(time.monotonic()-started)))),self.tick)

    def update_instructions(self):
        stage = self.progress.stage
        if stage == 1:
            self.heading.set(f'2 de 3 · mova o cursor · alvo {self.progress.visited+1} de 2')
            self.instruction.set('Aponte com o indicador e mova devagar até o ponto entrar no círculo azul. Se faltar espaço, retire a mão e volte numa posição confortável; o cursor fica onde estava.')
        elif stage == 2:
            self.heading.set('3 de 3 · junte e solte para clicar')
            self.instruction.set('Leve o ponto ao círculo central. Junte polegar e indicador: o cursor trava. Solte os dedos para clicar. Manter a pinça fechada não arrasta o cursor.')
        elif stage == 3:
            self.heading.set('Pronto · movimentos e clique praticados')
            self.instruction.set('Para rolar, junte indicador e médio e mova para cima/baixo. Com três dedos levantados: mova para os lados para trocar de área; para baixo para minimizar. Ctrl+Alt+G pausa.')

    def draw(self,point,progress=0.):
        self.canvas.delete('all')
        w = max(520,self.canvas.winfo_width())
        h = 205
        if self.progress.stage == 0:
            self.canvas.create_text(w/2,h/2,text='Levante só o indicador\npara aparecer o cursor',fill='#b5cad9',font=('sans',16),justify='center')
        target = self.progress.target
        if target:
            x,y = target[0]*w,target[1]*h
            self.canvas.create_oval(x-25,y-25,x+25,y+25,outline='#68b8ff',width=3)
            self.canvas.create_text(x,y+42,text='Clique aqui' if self.progress.stage==2 else 'Passe por aqui',fill='#b5cad9')
        if point:
            x,y = point[0]*w,point[1]*h
            self.canvas.create_oval(x-7,y-7,x+7,y+7,fill='#65e5d3',outline='white',width=2)
            self.canvas.create_arc(x-14,y-14,x+14,y+14,start=90,extent=-360*progress,style='arc',outline='white',width=3)
        if self.progress.done:
            self.canvas.create_text(w/2,h/2,text='Treino concluído',fill='#65e5d3',font=('sans',20,'bold'))

    def preview(self,frame,kp):
        import cv2
        display = cv2.resize(frame,(160,120))
        if self.mirror: display = cv2.flip(display,1)
        if kp is not None:
            for i in (0,4,8,12,16,20):
                x = float(kp[i][0])*160/frame.shape[1]
                y = float(kp[i][1])*120/frame.shape[0]
                if self.mirror: x=159-x
                cv2.circle(display,(round(x),round(y)),3,(80,230,200),-1)
        rgb = cv2.cvtColor(display,cv2.COLOR_BGR2RGB)
        photo = tk.PhotoImage(data=b'P6\n160 120\n255\n'+rgb.tobytes(),format='PPM')
        self.preview_label.configure(image=photo,text='')
        self.preview_label.image = photo

    def close(self,accepted=False):
        if self.closed: return
        self.pause()
        self.closed = True
        self.window.grab_release()
        self.window.destroy()
        self.on_close(accepted)
