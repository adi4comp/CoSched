import threading
import random
import time
from enum import Enum

class ThreadState(Enum):
    IDLE = 0
    RUNNING = 1
    BLOCKED = 2
    TERMINATED = 3

random.seed(time.time())
class Scheduler:
    def __init__(self,debug=False):
        self.lock = threading.Lock() 
        self.threads = [] 
        self.ready_queue = []
        self.state = {}
        self.blocked = []
        # self.thread_sync_dependency = []
        # self.thread_dependency_map = {}
        self.debug = debug

    def register(self, thread):
        self.threads.append(thread)
        self.ready_queue.append(thread)
        self.state[thread] = ThreadState.IDLE

    def pick_next_thread(self):
        if self.ready_queue:
            return random.choice(self.ready_queue)
        return None

    def run(self,thread):
        if self.state[thread] != ThreadState.BLOCKED:
            self.state[thread] = ThreadState.RUNNING   
            if self.debug:
                print(f"[Scheduler Info] Starting {thread.name} at {get_time()}")
            thread.run()
        if self.state[thread] == ThreadState.RUNNING:
            if self.debug:
                print(f"[Scheduler Info] Finished {thread.name} at {get_time()}")
            self.state[thread] = ThreadState.TERMINATED
            self.ready_queue.remove(thread)

    def start(self):
        if self.debug:
            print("Scheduler started at: ", get_time())
        while scheduler.ready_queue:
            if self.debug:
                print("Ready queue:", [t.name for t in self.ready_queue])
            thread = self.pick_next_thread()
            scheduler.run(thread)
            

    def check(self, thread):
        if thread in self.threads:
            return True
        else:
            return False

scheduler = Scheduler()

class ThreadWrapper(threading.Thread):
    def __init__(self, target=None, args=()):
        super().__init__(target=target, args=args)
    def start(self):
        scheduler.register(self)
    def run(self):
        if scheduler.state[self] == ThreadState.RUNNING:
            super().run()
        elif self in scheduler.threads:
            print(f"[Info] Thread {self.name} is in the queue")
        else:
            scheduler.register(self)
        
        
    def is_alive(self):
        if scheduler.state[self] == ThreadState.RUNNING or scheduler.state[self] == ThreadState.BLOCKED:
            return True
        else:
            return False
    def join(self, timeout = None):
        for t in scheduler.threads:
            if scheduler.state[t] == ThreadState.RUNNING:
                calling_thread = t
                break
    
        if scheduler.debug:
            print(f"Thread {calling_thread.name} is waiting for {self.name} to finish") 
        
        if scheduler.state[self] != ThreadState.TERMINATED:
            if scheduler.debug:
                print(f"Thread {calling_thread.name} is waiting for {self.name} to finish") 
            scheduler.ready_queue.remove(calling_thread)
            scheduler.state[calling_thread] = ThreadState.BLOCKED

        while True:    
            thread = scheduler.pick_next_thread()
            if thread == self:
                scheduler.run(self)
                scheduler.state[calling_thread] = ThreadState.IDLE
                scheduler.ready_queue.append(calling_thread)

            if thread == calling_thread and scheduler.state[self] == ThreadState.TERMINATED:
                scheduler.state[calling_thread] = ThreadState.RUNNING
                break

            if thread == None:
                print(f"Deadlock detected, thread {self.name} is waiting for {calling_thread.name} to finish")
                exit(1)

        
def new_thread(target, args=()):
    t = ThreadWrapper(target=target, args=args)
    return t

def task(id):    
    print(f"Thread {id} is going to sleep for 5 seconds")
    time.sleep(5)
    print(f"Thread {id} had a good sleep")

def task_special(thread):
    print(f"We will wait for {thread.name}")
    thread.join(thread)
    print(f"Looks like {thread.name} is done")

start_time = time.time()

def get_time():
    return (time.time() - start_time)

if __name__ == "__main__":
    threads = [new_thread(task,args=(i+1,)) for i in range(3)]
    threads.append(new_thread(task_special, args=(threads[2],)))
    threads.append(new_thread(task_special, args=(threads[3],)))
    for t in threads:
        scheduler.register(t)
    scheduler.start()