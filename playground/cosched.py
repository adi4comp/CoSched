import threading
import random
import time
from enum import Enum
from greenlet import greenlet

class ThreadState(Enum):
    IDLE = 0
    RUNNING = 1
    BLOCKED = 2
    TERMINATED = 3

class LockState(Enum):
    UNLOCKED = 0
    LOCKED = 1

random.seed(time.time())

class Scheduler:
    def __init__(self, debug=False):
        self.lock = threading.Lock() 
        self.threads = [] 
        self.ready_queue = []
        self.state = {}
        self.wait_join = {}
        self.locks = []
        self.lock_state = {}
        self.lock_holder = {}
        self.debug = debug    
        self.greenlets = {} 
        
        self.main_greenlet = greenlet(self._scheduler_loop)

    def _scheduler_loop(self):
        while self.ready_queue:
            thread = self.pick_next_thread()
            if thread:
                if self.state[thread] != ThreadState.BLOCKED:
                    self.state[thread] = ThreadState.RUNNING
                    
                    if thread in self.greenlets:
                        if self.debug:
                            print(f"[Scheduler Loop] Switching to {thread.name}")
                        self.greenlets[thread].switch()
                        if self.state[thread] == ThreadState.RUNNING:
                            if self.debug:
                                print(f"[Scheduler Loop] Thread {thread.name} finished execution")
                            self.state[thread] = ThreadState.TERMINATED
                            if thread in self.ready_queue:
                                self.ready_queue.remove(thread)
                    else:
                        self.preempt_thread(thread)

    def register(self, thread):
        self.threads.append(thread)
        self.ready_queue.append(thread)
        self.state[thread] = ThreadState.IDLE

    def pick_next_thread(self):
        if self.ready_queue:
            if self.debug:
                print("Available threads:", ", ".join([f"{i}: {t.name}-{i+1}" for i, t in enumerate(self.ready_queue)]))
            try:
                index = int(input("Enter the next thread index to run: "))
                return self.threads[index]
            except (ValueError, IndexError):
                print("Invalid index, enter again")
                return self.pick_next_thread()
        return None

    def run(self, thread):
        if self.debug:
            thread_names = [t.name for t in self.ready_queue]
            print(f"[Scheduler Info] Thread {thread.name} is chosen to run from the {thread_names} queue ")
        self.preempt_thread(thread)

    def start(self):
        if self.debug:
            print("Scheduler started at: ", get_time())
    
        self.main_greenlet.switch()
            
    def register_lock(self, lock):
        self.locks.append(lock)
        self.lock_state[lock] = LockState.UNLOCKED
        self.lock_holder[lock] = None
    
    def preempt_thread(self, thread):
        if thread not in self.greenlets:
            def thread_runner():
                if self.debug:
                    print(f"[Greenlet] Starting execution of {thread.name}")
                try:
                    if hasattr(thread, '_preserve_target') and thread._preserve_target:
                        thread._preserve_target(*thread._preserve_args, **thread._preserve_kwargs)
                    else:
                        thread.run()
                except Exception as e:
                    print(f"[ERROR] Exception in thread {thread.name}: {e}")
                finally:
                    if self.debug:
                        print(f"[Greenlet] Thread {thread.name} completed execution")
                    self.state[thread] = ThreadState.TERMINATED
                    if thread in self.wait_join:
                        self.state[self.wait_join[thread]] = ThreadState.IDLE
                        if self.wait_join[thread] not in self.ready_queue:
                            self.ready_queue.append(self.wait_join[thread])
                    if thread in self.ready_queue:
                        self.ready_queue.remove(thread)
                    
                    self.main_greenlet.switch()
            
            self.greenlets[thread] = greenlet(thread_runner, parent=self.main_greenlet)
            if self.debug:
                print(f"[Scheduler Info] Created greenlet for {thread.name}")
        
        self.state[thread] = ThreadState.RUNNING
        if self.debug:
            print(f"[Scheduler Info] Switching to {thread.name} at {get_time()}")
        
        self.greenlets[thread].switch()
        
        if self.debug:
            print(f"[Scheduler Info] Returned from {thread.name} at {get_time()}")


def get_calling_thread():
    for t in scheduler.threads:
        if scheduler.state[t] == ThreadState.RUNNING:
            return t
    if scheduler.debug:
        print("No calling thread found")
        print(f"Scheduler state: {scheduler.state}")
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
            
    def join(self, timeout=None):
        
        calling_thread = get_calling_thread()
        
        if scheduler.state[self] != ThreadState.TERMINATED:
            scheduler.wait_join[self] = calling_thread
            if scheduler.debug:
                print(f"[Join] Thread {calling_thread.name} is waiting for {self.name}")
            
            scheduler.state[calling_thread] = ThreadState.BLOCKED
            if calling_thread in scheduler.ready_queue:
                scheduler.ready_queue.remove(calling_thread)
            
        if scheduler.debug:
            print(f"[Join] Preempting Thread {calling_thread.name} for {self.name} to finish")
        scheduler.main_greenlet.switch()
        if scheduler.debug:
            print(f"[Join] Thread {calling_thread.name} resumed after {self.name} completion")
        return True
        
            


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
                if calling_thread in scheduler.ready_queue:
                    scheduler.ready_queue.remove(calling_thread)
                    
                holder_thread = scheduler.lock_holder[self]
                if scheduler.state[holder_thread] == ThreadState.TERMINATED:
                    raise RuntimeError(f"Thread {holder_thread.name} is terminated and didn't release the lock")
                
                # Switch to scheduler to let it run other threads
                scheduler.main_greenlet.switch()
                
                # When execution returns here, the lock should be available
                scheduler.lock_state[self] = LockState.LOCKED
                scheduler.lock_holder[self] = calling_thread
                return True
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
            return super().acquire(blocking, timeout)
            
    def release(self):
        super().release()
        
    def locked(self):
        return super().locked()


def new_thread(target, args=()):
    t = ThreadWrapper(target=target, args=args)
    # Set a name for better debugging
    t.name = f"Thread-{target.__name__}-{len(scheduler.threads)}"
    return t

def task(id):    
    print(f"Thread {id} is going to sleep for 2 seconds")
    time.sleep(2)
    print(f"Thread {id} had a good sleep")

def task_special(thread):
    print(f"We will wait for {thread.name}")
    thread.join()
    print(f"Looks like {thread.name} is done")

def task_special2(thread):
    print(f"Thread is going to randomfunc")
    thread.join()
    print(f"Thread is back from randomfunc")

start_time = time.time()

def get_time():
    return (time.time() - start_time)


scheduler = Scheduler(debug=False)
lock_1 = NewRLock()
lock_2 = NewLock()
lock_3 = NewLock()

if __name__ == "__main__":

    threads = [new_thread(task, args=(i+1,)) for i in range(3)]
    threads.append(new_thread(task_special, args=(threads[2],)))
    threads.append(new_thread(task_special2, args=(threads[3],)))
    

    for t in threads:
        scheduler.register(t)
        

    scheduler.start()