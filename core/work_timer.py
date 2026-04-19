import threading
import time


class WorkTimer:
    def __init__(self, notify_callback, work_limit_seconds=3 * 60 * 60):
        self.work_limit = work_limit_seconds
        self.notify = notify_callback

        self.start_time = time.time()
        self.running = False
        self._lock = threading.Lock()
        self.thread = threading.Thread(target=self._loop, daemon=True)

    def start(self):
        if self.running:
            return

        self.running = True
        self.reset()
        self.thread.start()

    def reset(self):
        # Вызывается при активности пользователя или после напоминания.
        with self._lock:
            self.start_time = time.time()

    def get_elapsed_seconds(self) -> int:
        with self._lock:
            return int(time.time() - self.start_time)

    def stop(self):
        self.running = False

    def _loop(self):
        while self.running:
            with self._lock:
                elapsed = time.time() - self.start_time

            if elapsed >= self.work_limit:
                self.notify()
                self.reset()

            time.sleep(30)
