"""Small native control panel. Camera stays off until an explicit Start."""
import gc
import os
import signal
import sys
import time
import tkinter as tk
from tkinter import messagebox, ttk

from .backends import create_mouse, set_dpi_awareness
from .gestures import GestureController
from . import __version__
from .preferences import Preferences


class CursorHint:
    """Small translucent, click-through pointer hint (no fullscreen overlay)."""
    def __init__(self, parent, mouse):
        self.parent, self.mouse = parent, mouse
        self.window = tk.Toplevel(parent)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.attributes('-topmost',True)
        self.window.attributes('-alpha',.65)
        self.window.configure(bg='#101820')
        self.canvas = tk.Canvas(self.window,width=28,height=28,bg='#101820',highlightthickness=0)
        self.canvas.pack()
        self.circle = self.canvas.create_oval(5,5,23,23,outline='#65e5d3',width=2)
        self.canvas.create_line(14,0,14,5,fill='#65e5d3')
        self.canvas.create_line(0,14,5,14,fill='#65e5d3')
        if sys.platform == 'win32':
            self.window.attributes('-transparentcolor','#101820')
        self.window.geometry('28x28+0+0')
        self.window.update_idletasks()
        self.configured = False

    def show(self, point, pressed=False):
        if point is None:
            self.hide()
            return
        if not hasattr(self.mouse,'passthrough'):
            # Native Wayland already draws the actual system pointer; an XWayland
            # overlay cannot be placed reliably across compositor windows.
            return
        width,height = self.mouse.size()
        origin_x = origin_y = 0
        if sys.platform == 'win32':
            origin_x = self.mouse.user.GetSystemMetrics(76)
            origin_y = self.mouse.user.GetSystemMetrics(77)
        x = origin_x + round(point[0]*(width-1)) - 14
        y = origin_y + round(point[1]*(height-1)) - 14
        # Keep the top-left anchor even on negative virtual coordinates. Tk's
        # bare -N form means a distance from the opposite screen edge.
        self.window.geometry(f'28x28+{x}+{y}')
        self.window.deiconify()
        if not self.configured:
            self.window.update_idletasks()
            self.mouse.passthrough(self.window.winfo_id())
            self.configured = True
        self.canvas.itemconfigure(self.circle,outline='#fbbf24' if pressed else '#65e5d3')

    def hide(self): self.window.withdraw()
    def close(self): self.window.destroy()


class Application:
    def __init__(self, root, camera=0, fps=15, preferences=None):
        self.root = root
        self.camera_index, self.fps = camera, fps
        self.camera = self.tracker = self.mouse = self.controller = self.hint = None
        self.closed = False
        self.running = False
        self.last_preview = self.last_status = 0.
        self.last_result = None
        self.frame_count = 0
        self.started = 0.
        self.job = None
        self.preferences = preferences if preferences is not None else Preferences()
        self.tutorial = None
        root.title('UniversalTouch')
        root.geometry('490x620')
        root.minsize(470,600)
        root.configure(bg='#101820')
        root.protocol('WM_DELETE_WINDOW',self.close)
        root.bind('<Escape>',lambda _: self.pause())
        root.bind('<Control-Alt-g>',lambda _: self.toggle())
        root.bind('<Control-Alt-G>',lambda _: self.close())
        style = ttk.Style(root)
        style.theme_use('clam')
        style.configure('TFrame',background='#101820')
        style.configure('TLabel',background='#101820',foreground='#e7edf3',font=('sans',10))
        style.configure('Title.TLabel',font=('sans',23,'bold'),foreground='#65e5d3')
        style.configure('TButton',font=('sans',11),padding=9)
        style.configure('TCheckbutton',background='#101820',foreground='#e7edf3',font=('sans',10))
        panel = ttk.Frame(root,padding=22)
        panel.pack(fill='both',expand=True)
        ttk.Label(panel,text='UniversalTouch',style='Title.TLabel').pack(anchor='w')
        ttk.Label(panel,text='Sua mão. Seu cursor. Tudo no dispositivo.').pack(anchor='w',pady=(2,18))
        self.status = tk.StringVar(value='Pausado · câmera desligada')
        self.metrics = tk.StringVar(value=f'v{__version__} · perfil econômico · até {fps} FPS')
        ttk.Label(panel,textvariable=self.status,wraplength=420,font=('sans',12,'bold')).pack(anchor='w')
        ttk.Label(panel,textvariable=self.metrics,foreground='#a5b5c7').pack(anchor='w',pady=(6,15))
        self.start_button = ttk.Button(panel,text='Iniciar gestos',command=self.toggle)
        self.start_button.pack(fill='x')
        ttk.Button(panel,text='Aprender os gestos · treino interativo',command=self.open_tutorial).pack(fill='x',pady=(8,0))
        ttk.Label(panel,text='Primeiro, mostre a mão aberta por um instante.',wraplength=420).pack(anchor='w',pady=(12,14))
        self.show_hint = tk.BooleanVar(value=True)
        self.show_preview = tk.BooleanVar(value=False)
        self.mirror = tk.BooleanVar(value=True)
        ttk.Checkbutton(panel,text='Indicador discreto junto ao cursor',variable=self.show_hint).pack(anchor='w',pady=3)
        ttk.Checkbutton(panel,text='Mostrar prévia da câmera (opcional)',variable=self.show_preview,command=self.preview_changed).pack(anchor='w',pady=3)
        ttk.Checkbutton(panel,text='Espelhar movimento horizontal',variable=self.mirror,command=self.mirror_changed).pack(anchor='w',pady=3)
        self.preview_label = ttk.Label(panel)
        help_text=('Indicador → mover o cursor\n'
                   'Polegar + indicador → clique; segure para arrastar\n'
                   'Polegar + médio → clique direito\n'
                   'Dois dedos erguidos → rolagem vertical\n'
                   'Punho fechado → soltar e parar o cursor')
        ttk.Label(panel,text=help_text,wraplength=420,justify='left').pack(anchor='w',pady=(18,10))
        ttk.Label(panel,text='Ctrl+Alt+G: iniciar/pausar\nCtrl+Alt+Shift+G: sair · Esc: pausar nesta janela',
                  foreground='#a5b5c7',wraplength=420).pack(anchor='w',pady=4)
        ttk.Label(panel,text='Ao fechar, câmera e processamento são encerrados.',foreground='#a5b5c7',wraplength=420).pack(anchor='w',pady=(12,0))
        self.root.after(200,self.setup_input)

    def setup_input(self):
        if self.closed: return
        try:
            self.mouse = create_mouse()
            self.controller = GestureController(self.mouse,mirror=self.mirror.get())
            self.hint = CursorHint(self.root,self.mouse)
            if not self.mouse.hotkeys_available:
                self.metrics.set(f'{self.mouse.name} · atalhos globais indisponíveis; use a janela')
            else:
                self.metrics.set(f'{self.mouse.name} · câmera desligada · até {self.fps} FPS')
        except Exception as exc:
            self.start_button.configure(state='disabled')
            self.status.set('Entrada do sistema indisponível')
            self.metrics.set(str(exc))
        self.poll_keys()
        if not self.preferences.tutorial_seen:
            self.root.after(100,self.open_tutorial)

    def open_tutorial(self):
        if self.closed: return
        if self.tutorial is not None:
            self.tutorial.window.lift()
            return
        self.pause()
        from .tutorial_ui import Tutorial
        self.tutorial = Tutorial(self.root,self.camera_index,self.tutorial_closed,
                                 fps=self.fps,mirror=self.mirror.get())

    def tutorial_closed(self,accepted):
        self.tutorial = None
        if accepted:
            try: self.preferences.accept_tutorial()
            except OSError:
                self.metrics.set('Não foi possível salvar a preferência. O tutorial reaparecerá ao abrir.')

    def poll_keys(self):
        if self.closed: return
        try:
            for action in self.mouse.hotkeys() if self.mouse else []:
                if action == 'quit':
                    self.close()
                    return
                self.toggle()
        except Exception:
            self.pause()
            self.metrics.set('Atalho indisponível · use os controles desta janela')
        if not self.closed: self.root.after(80,self.poll_keys)

    def toggle(self):
        if self.running: self.pause()
        else: self.start()

    def start(self):
        if self.running or not self.controller or self.closed: return
        if self.tutorial is not None: return
        if not self.preferences.tutorial_seen:
            self.open_tutorial()
            return
        self.status.set('Preparando câmera e modelos…')
        self.root.update_idletasks()
        try:
            from .vision import Camera, HandTracker
            self.tracker = HandTracker()
            self.camera = Camera(self.camera_index)
            self.controller.set_paused(False)
            self.running = True
            self.started, self.frame_count = time.monotonic(), 0
            self.start_button.configure(text='Pausar · desligar câmera')
            self.status.set('Mostre a mão aberta para ativar')
            self.tick()
        except Exception as exc:
            self.pause()
            self.status.set('Não foi possível iniciar')
            messagebox.showerror('UniversalTouch',str(exc),parent=self.root)

    def pause(self):
        self.running = False
        if self.job is not None:
            self.root.after_cancel(self.job)
            self.job = None
        if self.controller: self.controller.set_paused(True)
        if self.camera: self.camera.close()
        self.camera = self.tracker = None
        if self.hint: self.hint.hide()
        self.last_result = None
        self.preview_label.configure(image='')
        self.preview_label.image = None
        gc.collect()
        self.start_button.configure(text='Iniciar gestos')
        self.status.set('Pausado · câmera desligada')

    def mirror_changed(self):
        if self.controller:
            if self.running: self.pause()
            self.controller.mirror = self.mirror.get()

    def preview_changed(self):
        if self.show_preview.get():
            self.preview_label.pack(pady=8)
            self.root.geometry('490x780')
        else:
            self.preview_label.pack_forget()
            self.preview_label.configure(image='')
            self.preview_label.image = None
            self.root.geometry('490x620')

    def tick(self):
        self.job = None
        if not self.running or self.closed: return
        before = time.monotonic()
        try:
            frame = self.camera.latest()
            if frame is not None:
                kp = self.tracker(frame)
                result = self.controller.update(kp,frame.shape,before)
                self.last_result = result
                self.frame_count += 1
                if self.hint:
                    if self.show_hint.get() and result.pointer:
                        try:
                            self.hint.show(result.pointer,result.pressed)
                        except Exception:
                            self.show_hint.set(False)
                            self.hint.hide()
                    else: self.hint.hide()
                if before-self.last_status >= .20:
                    self.status.set(result.status)
                    fps = self.frame_count / max(.1,before-self.started)
                    self.metrics.set(f'{self.mouse.name} · {fps:.1f} FPS · imagem local 640×480')
                    self.last_status = before
                if self.show_preview.get() and before-self.last_preview >= .33:
                    self.preview(frame,kp)
                    self.last_preview = before
            elif before-self.camera.last_frame > 2.:
                raise RuntimeError('A câmera parou de fornecer imagens. Verifique a conexão ou a permissão.')
        except Exception as exc:
            self.pause()
            self.status.set('Pausado após erro · botões liberados')
            messagebox.showerror('UniversalTouch',str(exc),parent=self.root)
            return
        delay = max(1,round(1000*(1/self.fps-(time.monotonic()-before))))
        self.job = self.root.after(delay,self.tick)

    def preview(self,frame,kp):
        import cv2
        disp = cv2.resize(frame,(240,180))
        if self.mirror.get(): disp = cv2.flip(disp,1)
        if kp is not None:
            for index in (4,8,12):
                x,y = kp[index]
                x,y = round(float(x)*240/frame.shape[1]),round(float(y)*180/frame.shape[0])
                if self.mirror.get(): x = 239-x
                cv2.circle(disp,(x,y),3,(100,235,210),-1)
        rgb = cv2.cvtColor(disp,cv2.COLOR_BGR2RGB)
        image = tk.PhotoImage(data=b'P6\n240 180\n255\n'+rgb.tobytes(),format='PPM')
        self.preview_label.configure(image=image)
        self.preview_label.image = image

    def close(self):
        if self.closed: return
        try:
            if self.tutorial is not None:
                self.tutorial.close(False)
            self.pause()
        finally:
            self.closed = True
            try:
                if self.hint: self.hint.close()
                if self.mouse: self.mouse.close()
            finally:
                self.root.destroy()


def run(camera=0,fps=15,smoke_seconds=None):
    import tempfile
    lock_path = os.path.join(tempfile.gettempdir(),f'universaltouch-{os.getuid() if hasattr(os,"getuid") else os.environ.get("USERNAME","user")}.lock')
    lock = open(lock_path,'a+b')
    try:
        if sys.platform == 'win32':
            import msvcrt
            lock.seek(0)
            lock.write(b'0')
            lock.flush()
            lock.seek(0)
            msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        else:
            import fcntl
            fcntl.flock(lock,fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        lock.close()
        print('UniversalTouch já está aberto. Use Ctrl+Alt+G para iniciar/pausar.')
        return 0
    set_dpi_awareness()
    root = tk.Tk()
    app = Application(root,camera,fps)
    signal.signal(signal.SIGINT,lambda *_: app.close())
    signal.signal(signal.SIGTERM,lambda *_: app.close())
    if smoke_seconds: root.after(round(smoke_seconds*1000),app.close)
    try:
        root.mainloop()
    finally:
        if not app.closed: app.close()
        lock.close()
    return 0
