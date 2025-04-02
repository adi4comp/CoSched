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
    def __init__(self):
        self.lock = threading.Lock() 
        self.threads = [] 
        self.ready_queue = []
        self.state = []
        self.blocked = []
        self.thread_sync_dependency = []
        self.thread_dependency_map = {}

    def register(self, thread):
        self.threads.append(thread)
        self.ready_queue.append(thread)
        self.state.append(ThreadState.IDLE)

    def pick_next_thread(self):
        if self.ready_queue:
            return random.choice(self.ready_queue)
        return None

    def run(self,thread):
        if self.state[self.threads.index(thread)] != ThreadState.BLOCKED:
            self.state[self.threads.index(thread)] = ThreadState.RUNNING   
            print(f"[Scheduler] Running {thread.name}")
            thread.run()
        if self.state[self.threads.index(thread)] == ThreadState.RUNNING:
            self.state[self.threads.index(thread)] = ThreadState.TERMINATED
            print(f"[Scheduler] Thread {thread.name} finished")
            self.ready_queue.remove(thread)

    def start(self):
        print("Scheduler started")
        while scheduler.ready_queue:
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
        if self in scheduler.threads:
            print(f"Thread {self.name} is waiting to run")
        else:
            scheduler.register(self)
        if scheduler.state[scheduler.threads.index(self)] == ThreadState.RUNNING:
            print(f"Thread {self.name} is running")
            super().run()
        
    def is_alive(self):
        if self in scheduler.threads and self in scheduler.ready_queue:
            return True
        else:
            print(f"Thread finished execution {self.name}")
            return False
    def join(self, timeout = None):
        for t in scheduler.threads:
            if scheduler.state[scheduler.threads.index(t)] == ThreadState.RUNNING:
                calling_thread = t
                break

        print(f"Thread {calling_thread.name} is waiting for {self.name} to finish") 
        scheduler.state[scheduler.threads.index(calling_thread)] = ThreadState.BLOCKED
        if scheduler.state[scheduler.threads.index(self)] != ThreadState.TERMINATED:
            scheduler.ready_queue.remove(calling_thread)

        while True:    
            thread = scheduler.pick_next_thread()
            if thread == self:
                scheduler.run(self)
                scheduler.ready_queue.append(calling_thread)

            if thread == calling_thread and scheduler.state[scheduler.threads.index(self)] == ThreadState.TERMINATED:
                scheduler.state[scheduler.threads.index(calling_thread)] = ThreadState.RUNNING
                break

            if thread == None:
                print(f"Deadlock detected, thread {self.name} is waiting for {calling_thread.name} to finish")
                exit(1)

    def scheduler_join(self):
        super().join()
        

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


if __name__ == "__main__":
    threads = [new_thread(task,args=(i,)) for i in range(3)]
    threads.append(new_thread(task_special, args=(threads[2],)))
    threads.append(new_thread(task_special, args=(threads[3],)))
    for t in threads:
        scheduler.register(t)
    scheduler.start()