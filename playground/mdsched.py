import threading
import random
import time

class Scheduler:
    def __init__(self):
        self.lock = threading.Lock() 
        self.threads = [] 
        self.ready_queue = []

    def register(self, thread):
        self.threads.append(thread)
        self.ready_queue.append(thread)

    def pick_next_thread(self):
        if self.ready_queue:
            return random.choice(self.ready_queue)
        return None

    def run(self):
        print("Starting the scheduler")
        while self.ready_queue:
            print("Ready queue:", [t.name for t in self.ready_queue])
            thread = self.pick_next_thread()
            if thread:
                thread.start()
                print(f"[Scheduler] Running {thread.name}")
                thread.join()
                self.ready_queue.remove(thread)

scheduler = Scheduler()

class ThreadWrapper(threading.Thread):
    def run(self):
        while True:
            with scheduler.lock:
                super().run()
                break

def new_thread(target, args=()):
    t = ThreadWrapper(target=target, args=args)
    return t

def task():    
    print(f"Thread {threading.current_thread().name} running")
    time.sleep(1)
    print(f"Thread {threading.current_thread().name} done")

if __name__ == "__main__":
    threads = [new_thread(task) for _ in range(3)]
    
    for t in threads:
        scheduler.register(t)

    scheduler.run()