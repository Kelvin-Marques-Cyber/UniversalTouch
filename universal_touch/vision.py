"""Bounded local camera capture and OpenCV Zoo hand inference."""
import hashlib
from pathlib import Path
import threading
import time

import cv2
import numpy as np

from .vendor.mp_palmdet import MPPalmDet
from .vendor.mp_handpose import MPHandPose

MODELS = {
    'palm_detection_mediapipe_2023feb.onnx': '78ff51c38496b7fc8b8ebdb6cc8c1abb02fa6c38427c6848254cdaba57fcce7c',
    'handpose_estimation_mediapipe_2023feb.onnx': 'db0898ae717b76b075d9bf563af315b29562e11f8df5027a1ef07b02bef6d81c',
}


def verify_models():
    root = Path(__file__).resolve().parent / 'models'
    paths = []
    for name, expected in MODELS.items():
        path = root / name
        if not path.is_file():
            raise RuntimeError('Modelos ausentes. Execute scripts/fetch_models.py ou reinstale o pacote completo.')
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise RuntimeError(f'Modelo incompleto ou alterado: {name}. Baixe os modelos novamente.')
        paths.append(path)
    return paths


class HandTracker:
    PALM_IDS = [0,5,9,13,17,1,2]

    def __init__(self, threads=2):
        cv2.setNumThreads(max(1, min(2, threads)))
        cv2.ocl.setUseOpenCL(False)
        palm, hand = verify_models()
        self.detector = MPPalmDet(str(palm), scoreThreshold=.65)
        self.landmarker = MPHandPose(str(hand), confThreshold=.75)
        self.palm = None

    def _landmarks(self, frame, palm):
        result = self.landmarker.infer(frame, palm)
        if result is None:
            return None
        kp = result[4:67].reshape(21,3)[:,:2].astype(np.float32)
        if not np.isfinite(kp).all():
            return None
        pts = kp[self.PALM_IDS]
        self.palm = np.r_[pts.min(axis=0), pts.max(axis=0), pts.reshape(-1), 1.].astype(np.float32)
        return kp

    def __call__(self, frame):
        try:
            if self.palm is not None:
                kp = self._landmarks(frame, self.palm)
                if kp is not None:
                    return kp
                self.palm = None
            palms = self.detector.infer(frame)
            if len(palms) == 0:
                return None
            i = int(np.argmax((palms[:,2]-palms[:,0]) * (palms[:,3]-palms[:,1])))
            return self._landmarks(frame, palms[i])
        except cv2.error:
            # Cropping a hand partly outside the frame can fail. Drop tracking;
            # callers release held buttons, then reacquire instead of freezing.
            self.palm = None
            return None


class Camera:
    """Exactly one latest frame; no history, storage, network or frame queue."""
    def __init__(self, index=0):
        import sys
        backend = cv2.CAP_DSHOW if sys.platform == 'win32' else cv2.CAP_V4L2
        self.cap = cv2.VideoCapture(index, backend)
        if not self.cap.isOpened():
            self.cap.release()
            self.cap = cv2.VideoCapture(index)
        if not self.cap.isOpened():
            self.cap.release()
            raise RuntimeError(f'Não foi possível abrir a câmera {index}. Feche outros apps que a utilizam.')
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 15)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._latest = None
        self.last_frame = time.monotonic()
        self.thread = threading.Thread(target=self._capture, daemon=True, name='UniversalTouch-camera')
        self.thread.start()

    def _capture(self):
        while not self._stop.is_set():
            ok, frame = self.cap.read()
            if self._stop.is_set():
                break
            if not ok:
                self._stop.wait(.05)
                continue
            # Drivers may ignore the requested format; bound processing anyway.
            h, w = frame.shape[:2]
            if w > 640 or h > 480:
                frame = cv2.resize(frame, (int(w*min(640/w,480/h)), int(h*min(640/w,480/h))))
            with self._lock:
                self._latest = frame
                self.last_frame = time.monotonic()

    def latest(self):
        with self._lock:
            frame, self._latest = self._latest, None
            return frame

    def close(self):
        self._stop.set()
        self.thread.join(timeout=1.)
        self.cap.release()
        self.thread.join(timeout=1.)
        with self._lock:
            self._latest = None


def self_test():
    """Run both neural graphs on synthetic pixels, without hardware or input."""
    tracker = HandTracker()
    blank = np.zeros((480,640,3), dtype=np.uint8)
    tracker.detector.infer(blank)
    palm = np.array([200,150,400,350,300,330,250,250,300,200,350,250,375,300,250,300,225,300,.99], dtype=np.float32)
    tracker.landmarker.infer(blank, palm)
    return {'models': 'sha256 OK; both ONNX graphs executed', 'opencv': cv2.__version__, 'numpy': np.__version__, 'camera_used': False, 'input_injected': False}


def benchmark(seconds=10, camera_index=0):
    import statistics
    tracker = HandTracker()
    camera = Camera(camera_index)
    frames = hands = 0
    durations = []
    started, cpu_started = time.monotonic(), time.process_time()
    try:
        while time.monotonic() - started < seconds:
            tick = time.monotonic()
            frame = camera.latest()
            if frame is not None:
                before = time.perf_counter()
                kp = tracker(frame)
                durations.append((time.perf_counter()-before)*1000)
                hands += int(kp is not None)
                frames += 1
            elif time.monotonic() - camera.last_frame > 3.:
                raise RuntimeError('A câmera abriu, mas não entregou imagens.')
            time.sleep(max(.001, 1/15 - (time.monotonic()-tick)))
    finally:
        camera.close()
    elapsed = time.monotonic()-started
    # Read the running process directly. ru_maxrss can include pre-exec history
    # from process launchers, which is unrelated to this application's peak.
    from .memory import process_memory
    memory = process_memory()
    if not frames:
        raise RuntimeError('A câmera não entregou imagens durante a medição.')
    return {'seconds':round(elapsed,2), 'frames':frames, 'fps':round(frames/elapsed,2),
            'frames_with_hand':hands, 'median_inference_ms':round(statistics.median(durations),2),
            'cpu_percent_one_core':round(100*(time.process_time()-cpu_started)/elapsed,1),
            **memory, 'input_injected':False, 'frames_saved':False}
