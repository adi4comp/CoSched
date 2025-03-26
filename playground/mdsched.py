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
        self.thread_sync_dependency = []
        self.thread_dependency_map = {}

    def register(self, thread):
        self.threads.append(thread)
        self.ready_queue.append(thread)
        self.state.append(ThreadState.IDLE)

    def pick_next_thread(self):
        # if self.thread_sync_dependency:
        #     return self.thread_sync_dependency.pop()
        # if self.blocked:
        #     return self.blocked.pop()
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
            # self.state[self.threads.index(thread)] = ThreadState.TERMINATED
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
            # with scheduler.lock:
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
        # scheduler.lock.release()
        print(f"Thread {calling_thread.name} is waiting for {self.name} to finish") 
        scheduler.state[scheduler.threads.index(calling_thread)] = ThreadState.BLOCKED
        if scheduler.state[scheduler.threads.index(self)] == ThreadState.TERMINATED:
            scheduler.state[scheduler.threads.index(calling_thread)] = ThreadState.RUNNING
            return
        while True:    
            thread = scheduler.pick_next_thread()
            if thread == self:
                # scheduler.state[scheduler.threads.index(self)] = ThreadState.RUNNING
                scheduler.run(self)
                # scheduler.lock.acquire()
                scheduler.state[scheduler.threads.index(calling_thread)] = ThreadState.RUNNING
                break
        # for t in scheduler.threads:
        #     if scheduler.state[scheduler.threads.index(t)] == ThreadState.RUNNING:
        #         thread = t
        #         break
        #     else:
        #         thread = None
        # scheduler.state[scheduler.threads.index(thread)] = ThreadState.BLOCKED
        # scheduler.thread_sync_dependency.append(self)
        # if thread in scheduler.thread_sync_dependency:
        #     scheduler.thread_sync_dependency.remove(thread)
        # scheduler.blocked.append(thread)
        # with scheduler.lock:
        #     scheduler.run()
        # scheduler.thread_dependency_map[thread].append(self)
        # while scheduler.state[scheduler.threads.index(thread)] != ThreadState.TERMINATED:
        #     print(f"Thread {thread.name} is waiting for {self.name} to finish")
        #     time.sleep(0.1)
        # super().join(timeout)
    def scheduler_join(self):
        super().join()
        

def new_thread(target, args=()):
    t = ThreadWrapper(target=target, args=args)
    return t

def task():    
    print(f"Thread {threading.current_thread().name} running")
    time.sleep(1)
    print(f"Thread {threading.current_thread().name} done")

def task_special(thread):
    print(f"Thread {threading.current_thread().name} waiting for thread {thread.name}")
    thread.join(thread)
    print(f"Thread {threading.current_thread().name} finished waiting")


if __name__ == "__main__":
    threads = [new_thread(task) for _ in range(3)]
    threads.append(new_thread(task_special, args=(threads[2],)))
    threads.append(new_thread(task_special, args=(threads[3],)))
    for t in threads:
        scheduler.register(t)

    scheduler.start()