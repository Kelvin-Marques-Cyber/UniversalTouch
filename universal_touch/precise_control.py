"""Index pointing, frozen pinch clicks, two-finger scroll and three-finger shortcuts."""
from collections import deque
import math

from .gestures import Result,distance


class PreciseController:
    def __init__(self,mouse,*,mirror=True,gain=1.8):
        self.mouse,self.mirror,self.gain=mouse,mirror,gain
        self.paused=True
        self.pointer=None
        self.origin=self.origin_pointer=None
        self.history=deque(maxlen=3)
        self.armed=False
        self.ready=0
        self.left_down=False
        self.action='left'
        self.pinch=None
        self.pinch_since=0.
        self.pinch_valid=False
        self.resume_at=0.
        self.last_time=None
        self.scroll_y=None
        self.scroll_at=0.
        self.shortcut_origin=None
        self.shortcut_since=0.
        self.shortcut_fired=False
        self.drag_palm=self.drag_pointer=None
        self.mode='none'

    def _reset(self):
        if self.left_down:self.mouse.release('left')
        self.left_down=False
        self.armed=False
        self.ready=0
        self.pinch=None
        self.pinch_valid=False
        self.origin=None
        self.history.clear()
        self.last_time=None
        self.scroll_y=None
        self.shortcut_origin=None
        self.shortcut_fired=False
        self.action='left'
        self.mode='none'

    def set_paused(self,paused):self._reset();self.paused=bool(paused)
    def close(self):self.set_paused(True)
    def set_action(self,action):
        if action not in ('left','right','drag'):raise ValueError('Invalid mouse action')
        self.action=action

    def _result(self,status,progress=0.):return Result(status,self.pointer,self.left_down,progress)

    def update(self,kp,shape,now):
        if self.paused:return Result('Pausado · câmera desligada')
        try:
            valid=(kp is not None and len(kp)==21 and shape[0]>0 and shape[1]>0 and math.isfinite(now)
                   and all(len(p)>=2 and all(math.isfinite(float(v)) for v in p[:2]) for p in kp))
        except (TypeError,ValueError,IndexError):valid=False
        if not valid:
            self._reset()
            return Result('Mostre o indicador para mover o cursor')
        scale=max(distance(kp[5],kp[17]),distance(kp[0],kp[9]))
        if scale<20:
            self._reset()
            return Result('Aproxime a mão da câmera')
        extended=[distance(kp[t],kp[0])>distance(kp[j],kp[0])*1.10 for t,j in [(8,6),(12,10),(16,14),(20,18)]]
        index_only=extended[0] and not any(extended[1:])
        left=distance(kp[4],kp[8])/scale
        palm=tuple(sum(float(kp[i][axis]) for i in (5,9,13,17))/4 for axis in (0,1))

        if not self.armed:
            self.ready=self.ready+1 if index_only and left>.72 else 0
            if self.ready<2:return Result('Levante só o indicador · os outros dedos ficam relaxados')
            self.armed=True

        # Pinch is evaluated BEFORE any fingertip movement. Even an approaching
        # pinch freezes the cursor; normal clicks are emitted only after release.
        if self.pinch is not None:
            ratio=left
            if ratio<.72:
                if now-self.pinch_since>=.08:
                    self.pinch_valid=True
                    if self.action=='drag' and not self.left_down and self.pinch=='left':
                        self.mouse.press('left');self.left_down=True
                        self.drag_palm=palm;self.drag_pointer=self.pointer
                if self.left_down and self.drag_pointer is not None:
                    dx=(palm[0]-self.drag_palm[0])/shape[1]*(-1 if self.mirror else 1)
                    dy=(palm[1]-self.drag_palm[1])/shape[0]
                    self.pointer=tuple(max(0.,min(1.,v+d*self.gain)) for v,d in zip(self.drag_pointer,(dx,dy)))
                    self.mouse.move_to(self.pointer)
                    return self._result('Arrastando · solte a pinça para soltar',1.)
                return self._result('Clique preparado · solte os dedos para clicar',1.)
            if self.left_down:
                self.mouse.release('left');self.left_down=False
            elif self.pinch_valid:
                self.mouse.click(self.action if self.action=='right' else self.pinch)
            self.action='left'
            self.pinch=None
            self.pinch_valid=False
            self.resume_at=now+.20
            self.origin=None
            self.history.clear()
            return self._result('Clique feito · indicador para mover',1.)

        if left<.30 and not any(extended[1:]):
            self.pinch='left'
            self.pinch_since=now
            self.pinch_valid=False
            self.mode='pinch'
            return self._result('Pinça · cursor travado',1.)

        three=all(extended[:3]) and not extended[3]
        two=all(extended[:2]) and not any(extended[2:])
        if three:
            self.origin=None
            self.scroll_y=None
            if self.mode!='shortcut':
                self.shortcut_origin=palm;self.shortcut_since=now;self.shortcut_fired=False
            self.mode='shortcut'
            if not self.shortcut_fired and now-self.shortcut_since>=.15:
                dx=(palm[0]-self.shortcut_origin[0])/scale*(-1 if self.mirror else 1)
                dy=(palm[1]-self.shortcut_origin[1])/scale
                action=None
                if abs(dx)>.55 and abs(dx)>abs(dy)*1.3:action='workspace_next' if dx>0 else 'workspace_previous'
                elif dy>.60 and dy>abs(dx)*1.3:action='minimize'
                if action:
                    self.shortcut_fired=True
                    available=getattr(self.mouse,'perform_action',lambda _:False)(action)
                    return self._result('Atalho executado · solte a pose para repetir' if available else 'Atalho indisponível nesta sessão')
            return self._result('Três dedos: lados = outra área · para baixo = minimizar')
        self.shortcut_origin=None
        self.shortcut_fired=False

        if two:
            self.origin=None
            joined=distance(kp[8],kp[12])/scale<(.72 if self.mode=='scroll' else .50)
            if not joined:
                self.mode='two';self.scroll_y=None
                return self._result('Aproxime indicador e médio para rolar')
            y=(float(kp[8][1])+float(kp[12][1]))/2
            if self.mode!='scroll':self.scroll_y=y;self.scroll_at=now
            self.mode='scroll'
            unit=max(8.,scale*.12)
            steps=int((self.scroll_y-y)/unit)
            if steps and now-self.scroll_at>=.07:
                steps=max(-3,min(3,steps));self.mouse.scroll(steps)
                self.scroll_y-=steps*unit;self.scroll_at=now
            return self._result('Rolagem · mova dois dedos juntos para cima/baixo')
        self.scroll_y=None
        if not index_only:
            self.mode='none';self.history.clear();self.origin=None
            return self._result('Só o indicador para mover · pinça para clicar')
        if left<.58:
            return self._result('Preparando pinça · cursor travado')
        if now<self.resume_at:return self._result('Clique feito · aguardando soltar os dedos')
        tip=(float(kp[8][0])/shape[1],float(kp[8][1])/shape[0])
        tip=(1-tip[0] if self.mirror else tip[0],tip[1])
        if self.origin is None:self.history.clear()
        self.history.append(tip)
        if self.origin is None:
            self.origin=tip;self.origin_pointer=self.pointer or (.5,.5)
            self.pointer=self.origin_pointer;self.last_time=now
        median=tuple(sorted(p[axis] for p in self.history)[len(self.history)//2] for axis in (0,1))
        target=tuple(max(0.,min(1.,p+(v-o)*self.gain)) for p,v,o in zip(self.origin_pointer,median,self.origin))
        dt=max(.001,min(.20,now-self.last_time))
        speed=distance(target,self.pointer)/dt
        alpha=1-math.exp(-2*math.pi*min(12.,1.0+4*speed)*dt)
        self.pointer=tuple(p+alpha*(v-p) for p,v in zip(self.pointer,target))
        self.last_time=now;self.mode='point'
        self.mouse.move_to(self.pointer)
        return self._result('Indicador · movendo o cursor')
