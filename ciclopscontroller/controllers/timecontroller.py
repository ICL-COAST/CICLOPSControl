from PySide6.QtCore import QObject, QMutex, QTimer, Qt, Slot, QMutexLocker
from datetime import datetime, timedelta, timezone
from time import perf_counter


class TimeController(QObject):
    def __init__(self) -> None:
        super().__init__()
        self._timer: QTimer | None = None
        self._epoch = datetime(2025, 7, 14, 22, 24, 0)
        self._time_since_epoch: float = 0
        self._speed: float = 1
        self._reference_counter: float = 0
        self._reference_time: float = 0
        self._cycles = 0
        self._running = False
        self._mutex = QMutex()

    def initialize_timer(self) -> None:
        if self._timer is None:
            self._timer = QTimer(timerType=Qt.TimerType.PreciseTimer)
            self._timer.timeout.connect(self.run)

    def get_datetime(self) -> datetime:
        with QMutexLocker(self._mutex):
            time = self._epoch + timedelta(seconds=self._time_since_epoch)
        return time
    
    def get_running(self) -> bool:
        with QMutexLocker(self._mutex):
            return self._running
    
    Slot()
    def start_playback(self) -> None:
        if self._timer is None:
            raise Exception("Timer not initialized. Call initialize_timer() first.")
        with QMutexLocker(self._mutex):
            self._reference_counter = perf_counter()
            self._reference_time = self._time_since_epoch
            self._running = True
        self._timer.start(1)
        

    Slot()
    def stop_playback(self) -> None:
        if self._timer is None:
            raise Exception("Timer not initialized. Call initialize_timer() first.")
        self._timer.stop()
        with QMutexLocker(self._mutex):
            self._running = False

    Slot()
    def run(self) -> None:
        with QMutexLocker(self._mutex):
            current_counter = perf_counter()
            elapsed_real_time = current_counter - self._reference_counter

            self._time_since_epoch = self._reference_time + elapsed_real_time * self._speed

            if self._cycles % 1000 == 0:
                print(f"{self._time_since_epoch:.2f} seconds, Cycles: {self._cycles}, speed: {self._speed}x, Real Time = {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%f')[:-2]}, Counter = {current_counter-self._reference_counter:.2f}, Reference Time = {self._reference_time:.2f}")

            self._cycles += 1
        
    Slot()
    def set_speed(self, speed):
        with QMutexLocker(self._mutex):
            current_counter = perf_counter()
            elapsed_real_time = current_counter - self._reference_counter

            self._reference_time += elapsed_real_time * self._speed
            self._reference_counter = current_counter
            self._speed = speed
        
    Slot()
    def set_time(self, now:bool=False, time_since_epoch:float=0) -> None:
        with QMutexLocker(self._mutex):
            if now:
                self._time_since_epoch = (datetime.now(timezone.utc) - self._epoch).seconds
            else:
                self._time_since_epoch = time_since_epoch

            self._reference_counter = perf_counter()
            self._reference_time = self._time_since_epoch

    Slot()
    def set_epoch(self, new_datetime: datetime):
        self.stop_playback()
        with QMutexLocker(self._mutex):
            self._epoch = new_datetime
            self._time_since_epoch = 0
            self._reference_counter = perf_counter()
            self._reference_time = 0
