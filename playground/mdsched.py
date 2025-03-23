import threading
import random
import time
from enum import Enum

class ThreadState(Enum):
    IDLE = 0
    RUNNING = 1
    BLOCKED = 2
    TERMINATED = 3

class Scheduler:
    def __init__(self):
        self.lock = threading.Lock() 
        self.threads = [] 
        self.ready_queue = []
        self.state = []
        self.blocked = []

    def register(self, thread):
        self.threads.append(thread)
        self.ready_queue.append(thread)
        self.state.append(ThreadState.IDLE)

    def pick_next_thread(self):
        if self.blocked:
            return self.blocked.pop()
        if self.ready_queue:
            return random.choice(self.ready_queue)
        return None

    def run(self):
        print("Starting the scheduler")
        while self.ready_queue:
            print("Ready queue:", [t.name for t in self.ready_queue])
            thread = self.pick_next_thread()
            self.state[self.threads.index(thread)] = ThreadState.RUNNING
            print(f"[Scheduler] Running {thread.name}")
            thread.run()
            if self.state[self.threads.index(thread)] == ThreadState.RUNNING:
                self.state[self.threads.index(thread)] = ThreadState.TERMINATED
                print(f"[Scheduler] Thread {thread.name} finished")
            self.ready_queue.remove(thread)
            self.state[self.threads.index(thread)] = ThreadState.TERMINATED

    def check(self, thread):
        if thread in self.threads:
            return True
        else:
            return False

scheduler = Scheduler()

class ThreadWrapper(threading.Thread):  
    def start(self):
        scheduler.register(self)
    def run(self):
        if self in scheduler.threads:
            print(f"Thread {self.name} is waiting to run")
        else:
            scheduler.register(self)
        if scheduler.state[scheduler.threads.index(self)] == ThreadState.RUNNING:
            with scheduler.lock:
                print(f"Thread {self.name} is running")
                super().run()
        
    def is_alive(self):
        if self in scheduler.threads and self in scheduler.ready_queue:
            return True
        else:
            print(f"Thread finished execution {self.name}")
            return False
    def join(self,thread, timeout = None):
        scheduler.state[scheduler.threads.index(self)] = ThreadState.BLOCKED
        while scheduler.state[scheduler.threads.index(thread)] != ThreadState.TERMINATED:
            time.sleep(0.1)
        scheduler.blocked.append(self)
    
        

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