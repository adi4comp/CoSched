import threading
import random
import time
from enum import Enum

class ThreadState(Enum):
    IDLE = 0
    RUNNING = 1
    BLOCKED = 2
    WAITING = 3
    TERMINATED = 4

class LockState(Enum):
    UNLOCKED = 0
    LOCKED = 1

random.seed(time.time())
class Scheduler:
    def __init__(self,debug=False):
        self.lock = threading.Lock() 
        self.threads = [] 
        self.ready_queue = []
        self.state = {}
        self.blocked = []
        self.locks = []
        self.lock_state = {}
        self.lock_holder = {}
        self.debug = debug

    def register(self, thread):
        self.threads.append(thread)
        self.ready_queue.append(thread)
        self.state[thread] = ThreadState.IDLE

    def pick_next_thread(self):
        if self.ready_queue:
            # return random.choice(self.ready_queue)

            index = int(input("Enter the next thread index to run: "))
            return self.threads[index]
        return None

    def run(self,thread):
        if self.debug:
            thread_names = [t.name for t in self.ready_queue]
            print(f"[Scheduler Info] Thread {thread.name} is chosen from the {thread_names} queue ")
        if self.state[thread] != ThreadState.BLOCKED:
            self.state[thread] = ThreadState.RUNNING
            # print(f"[Scheduler Info] Running {thread.name} at {get_time()}")   
            # if self.debug:
            #     print(f"[Scheduler Info] Starting {thread.name} at {get_time()}")
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
            # if self.debug:
            #     print("Ready queue:", [t.name for t in self.ready_queue])
            thread = self.pick_next_thread()
            scheduler.run(thread)
            
    def register_lock(self, lock):
        self.locks.append(lock)
        self.lock_state[lock] = LockState.UNLOCKED
        self.lock_holder[lock] = None

    # def check(self, thread):
    #     if thread in self.threads:
    #         return True
    #     else:
    #         return False


def get_calling_thread():
    for t in scheduler.threads:
            if scheduler.state[t] == ThreadState.RUNNING:
                return t
    if scheduler.debug:
        print("No calling thread found")
        print (f"Scheduler state: {scheduler.state}")
    return None
class ThreadWrapper(threading.Thread):
    def __init__(self, target=None, args=()):
        super().__init__(target=target, args=args)
        self._preserve_target = self._target
        self._preserve_args = self._args
        self._preserve_kwargs = self._kwargs

    def start(self):
        scheduler.register(self)
    def run(self):
        if scheduler.state[self] == ThreadState.RUNNING:
            try:
                super().run()
            except AttributeError:
                if not hasattr(self, '_target'):
                    self._target = self._preserve_target
                if not hasattr(self, '_args'):
                    self._args = self._preserve_args
                if not hasattr(self, '_kwargs'):
                    self._kwargs = self._preserve_kwargs
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
        # if scheduler.debug:
        #     print(f"Thread join called for {self.name}")
        calling_thread = get_calling_thread()
    
        if scheduler.debug:
            print(f"Thread {calling_thread.name} is waiting for {self.name} to finish") 
        
        if scheduler.state[self] != ThreadState.TERMINATED:
            # if scheduler.debug:
            #     print(f"Thread {calling_thread.name} is waiting for {self.name} to finish") 
            scheduler.ready_queue.remove(calling_thread)
            scheduler.state[calling_thread] = ThreadState.BLOCKED

        while True:    
            thread = scheduler.pick_next_thread()
            if thread == self:
                scheduler.run(thread)
                scheduler.state[calling_thread] = ThreadState.WAITING
                scheduler.ready_queue.append(calling_thread)
                return True
            elif thread == calling_thread and scheduler.state[self] == ThreadState.TERMINATED:
                scheduler.state[calling_thread] = ThreadState.RUNNING
                return True
            elif thread == None:
                if scheduler.state[calling_thread] != ThreadState.TERMINATED:
                    raise RuntimeError(f"Deadlock detected, thread {self.name} is waiting for {calling_thread.name} to terminate")
                else:
                    return True
            elif scheduler.state[thread] == ThreadState.WAITING:
                continue
            else:
                scheduler.run(thread)   
class NewLock():
    def __init__(self):
        self.locked = False
        scheduler.register_lock(self)
        
    def acquire(self, blocking=True, timeout=-1):
        if blocking:
            if scheduler.lock_state[self]==LockState.UNLOCKED and scheduler.lock_holder[self] == None:
                scheduler.lock_state[self] = LockState.LOCKED
                scheduler.lock_holder[self] = get_calling_thread()
                return True
            else:
                calling_thread = get_calling_thread()
                scheduler.state[calling_thread] = ThreadState.BLOCKED
                scheduler.ready_queue.remove(calling_thread)
                holder_thread = scheduler.lock_holder[self]
                if scheduler.state[holder_thread] == ThreadState.TERMINATED:
                    raise RuntimeError(f"Thread {holder_thread.name} is terminated and didnt release the lock")
                
                while True:
                    thread = scheduler.pick_next_thread()
                    # if scheduler.debug:
                    #     print(f"The next thread to execute when waiting for lock to be release is {thread.name}")
                    if thread == holder_thread:
                        scheduler.run(holder_thread)
                        scheduler.state[calling_thread] = ThreadState.WAITING
                        scheduler.ready_queue.append(calling_thread)
                    
                    elif thread == calling_thread and scheduler.lock_state[self] == LockState.UNLOCKED:
                        scheduler.state[calling_thread] = ThreadState.RUNNING
                        return True
                    
                    elif thread == None:
                        raise RuntimeError(f"Deadlock detected, thread {calling_thread.name} is waiting for {holder_thread.name} to release the lock")
                    elif scheduler.state[thread] != ThreadState.WAITING:
                        scheduler.run(thread)

                  
        else:
            if scheduler.lock_state[self]==LockState.UNLOCKED and scheduler.lock_holder[self] == None:
                scheduler.lock_state[self] = LockState.LOCKED
                scheduler.lock_holder[self] = get_calling_thread()
                return True
            else:
                return False
    def release(self):
        calling_thread = get_calling_thread()
        if scheduler.lock_state[self] == LockState.LOCKED and scheduler.lock_holder[self] == get_calling_thread():
            scheduler.lock_state[self] = LockState.UNLOCKED
            scheduler.lock_holder[self] = None
            return True
        elif scheduler.lock_state[self]==LockState.LOCKED and scheduler.lock_holder[self] != get_calling_thread():
            raise RuntimeError(f"Cannot release a lock that is not held (held by {scheduler.lock_holder[self]}) by the calling thread {calling_thread.name}")
        elif scheduler.lock_state[self] == LockState.UNLOCKED:
            raise RuntimeError(f"Cannot release an unlocked lock {calling_thread.name} ")
        
    def locked(self):
        if scheduler.lock_state[self] == LockState.LOCKED:
            return True
        else:   
            return False


class NewRLock(NewLock):
    def __init__(self):
        super().__init__()
    def acquire(self, blocking=True, timeout=-1):
        if scheduler.lock_state[self]==LockState.LOCKED and scheduler.lock_holder[self] == get_calling_thread():
            return True
        else:
            super().acquire(blocking, timeout)
    def release(self):
        super().release()
    def locked(self):
        super().locked()


def new_thread(target, args=()):
    t = ThreadWrapper(target=target, args=args)
    return t

def task(id):    
    # print(f"Thread {id} is going to sleep for 2 seconds")
    # lock_1.acquire()
    # lock_1.acquire()
    time.sleep(2)
    # lock_1.release()
    # print(f"Thread {id} had a good sleep")

def task_special(thread):
    # print(f"We will wait for {thread.name}")
    # lock_2.acquire()
    # lock_2.acquire()
    thread.join(thread)
    # lock_2.release()
    # print(f"Looks like {thread.name} is done")

def task_special2(thread):
    # print(f"We will wait for {thread.name}")
    # lock_3.acquire()
    print(f"Thread is going to ramdomfunc")
    thread.join()
    print(f"Thread is back from randomfunc")
    # lock_3.release()
    # print(f"Looks like {thread.name} is done")

start_time = time.time()

def get_time():
    return (time.time() - start_time)

scheduler = Scheduler(debug=True)
lock_1 = NewRLock()
lock_2 = NewLock()
lock_3 = NewLock()


if __name__ == "__main__":
    threads = [new_thread(task,args=(i+1,)) for i in range(3)]
    threads.append(new_thread(task_special, args=(threads[2],)))
    threads.append(new_thread(task_special2, args=(threads[3],)))
    for t in threads:
        scheduler.register(t)
    scheduler.start()