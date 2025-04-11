import threading
import random
import time
import sys
from enum import Enum
from greenlet import greenlet

class ThreadState(Enum):
    IDLE = 0
    RUNNING = 1
    BLOCKED = 2
    TERMINATED = 3


random.seed(time.time())

class Scheduler:
    def __init__(self, debug=False):
        self.lock = threading.Lock() 
        self.threads = [] 
        self.ready_queue = []
        self.state = {}
        self.wait_join = {}
        self.lock_state = {}
        self.lock_holder = {}
        self.lock_queue = {}
        self.rlock_counter = {}
        self.debug = debug    
        self.greenlets = {} 
        self.policy = 1
        self.main_greenlet = greenlet(self._scheduler_loop)
        self.schedule = []
        self.thread_priority = {}

    def set_policy(self, policy):
        self.policy = policy    
    def verbose(self):
        self.debug = True
    def _scheduler_loop(self):
        while self.ready_queue:
            thread = self.pick_next_thread()
            self.schedule.append(thread)
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

        error = []
        for t in self.threads:
            if self.state[t] != ThreadState.TERMINATED:
                error.append(t)

        print(f"[Scheduler Loop] Scheduled Picked This time: {'-> '.join([t.name for t in self.schedule])}")
        if error:
            raise RuntimeError(f"[Scheduler Loop] Error: Threads {', '.join([t.name for t in error])} are not terminated due to deadlock")
    def register(self, thread):
        self.threads.append(thread)
        self.ready_queue.append(thread)
        self.state[thread] = ThreadState.IDLE
        self.thread_priority[thread] = 0

    def pick_next_thread(self):
        if self.ready_queue:
            if self.debug:
                print("Available threads:", ", ".join([f"{i}: {t.name}-{i+1}" for i, t in enumerate(self.ready_queue)]))

            match self.policy:
                case 0:
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
                case 1:
                    return random.choice(self.ready_queue)
                case 2:
                    last_thread = self.schedule[-1] if self.schedule else None
                    if self.ready_queue:
                        if last_thread:
                            self.thread_priority[last_thread] -= 1
                        max_priority = max(self.thread_priority.values())
                        max_priority_threads = [t for t, p in self.thread_priority.items() if p == max_priority]
                        return random.choice(max_priority_threads)
                    else:
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
        self.lock_holder[lock] = None
        self.lock_queue[lock] = []
    
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
                    self.state[thread] = ThreadState.TERMINATED
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
            # if scheduler.debug:
            print(f"[Join] Thread {calling_thread.name} is waiting for {self.name}")
            
            scheduler.state[calling_thread] = ThreadState.BLOCKED
            if calling_thread in scheduler.ready_queue:
                scheduler.ready_queue.remove(calling_thread)
        
        else:
            scheduler.state[calling_thread] = ThreadState.IDLE    
        if scheduler.debug:
            print(f"[Join] Preempting Thread {calling_thread.name} for {self.name} to finish")
        scheduler.main_greenlet.switch()
        if scheduler.debug:
            print(f"[Join] Thread {calling_thread.name} resumed after {self.name} completion")
        return True
        
            


class Lock():
    def __init__(self):
        self.locked = False
        scheduler.register_lock(self)
        
    def acquire(self, blocking=True, timeout=-1):
        if blocking:
            if not self.locked and scheduler.lock_holder[self] == None:
                self.locked = True
                scheduler.lock_holder[self] = get_calling_thread()
                scheduler.state[get_calling_thread()] = ThreadState.IDLE
                scheduler.main_greenlet.switch()
                return True
            else:
                if scheduler.debug:
                    print(f"[Acquire] Lock is already held by {scheduler.lock_holder[self]}")
                calling_thread = get_calling_thread()
                scheduler.state[calling_thread] = ThreadState.BLOCKED
                if calling_thread in scheduler.ready_queue:
                    scheduler.ready_queue.remove(calling_thread)
                    
                holder_thread = scheduler.lock_holder[self]
                if scheduler.state[holder_thread] == ThreadState.TERMINATED:
                    scheduler.state[get_calling_thread] = ThreadState.TERMINATED
                    raise RuntimeError(f"[Resource Starvation] Thread {holder_thread.name} is terminated and didn't release the lock")
                
                scheduler.lock_queue[self].append(calling_thread)
                scheduler.main_greenlet.switch()
                self.acquire(blocking, timeout)
                
            
            
                
        else:
            if not self.locked and scheduler.lock_holder[self] == None:
                self.locked = True
                scheduler.lock_holder[self] = get_calling_thread()
                scheduler.main_greenlet.switch()
                return True
            else:
                scheduler.main_greenlet.switch()
                return False
                
    def release(self):
        calling_thread = get_calling_thread()
        if self.locked and scheduler.lock_holder[self] == get_calling_thread():
            self.locked = False
            scheduler.lock_holder[self] = None
            scheduler.state[calling_thread] = ThreadState.IDLE
            if calling_thread not in scheduler.ready_queue:
                scheduler.ready_queue.append(calling_thread)
            if scheduler.lock_queue[self]:
                next_thread = scheduler.lock_queue[self].pop(0)
                scheduler.state[next_thread] = ThreadState.IDLE
                if next_thread not in scheduler.ready_queue:
                    scheduler.ready_queue.append(next_thread)
                if scheduler.debug:
                    print(f"[Release] Lock released by {calling_thread.name}, waking up {next_thread.name}")
            else:
                if scheduler.debug:
                    print(f"[Release] Lock released by {calling_thread.name}, no threads waiting")

        elif self.locked and scheduler.lock_holder[self] != get_calling_thread():
            scheduler.state[get_calling_thread] = ThreadState.TERMINATED
            raise RuntimeError(f"Cannot release a lock that is not held (held by {scheduler.lock_holder[self]}) by the calling thread {calling_thread.name}")
        
        elif not self.locked:
            scheduler.state[get_calling_thread] = ThreadState.TERMINATED
            raise RuntimeError(f"Cannot release an unlocked lock {calling_thread.name} ")
        
        scheduler.main_greenlet.switch()
               
    def locked(self):
        if self.locked:
            return True
        else:   
            return False


class RLock(Lock):
    def __init__(self):
        super().__init__()
        scheduler.rlock_counter[self] = 0
        
    def acquire(self, blocking=True, timeout=-1):
        if scheduler.rlock_counter[self]==0:
            scheduler.rlock_counter[self] = 1
        if self.locked and scheduler.lock_holder[self] == get_calling_thread():
            scheduler.rlock_counter[self] += 1
            scheduler.main_greenlet.switch()
            return True
        else:
            return super().acquire(blocking, timeout)
            
    def release(self):
        if self.locked and scheduler.lock_holder[self] == get_calling_thread():
            scheduler.rlock_counter[self] -= 1
            if scheduler.rlock_counter[self] == 0:
                super().release()
        else:
            raise RuntimeError(f"Cannot release a lock that is not held (held by {scheduler.lock_holder[self]}) by the calling thread {get_calling_thread().name}")
        scheduler.main_greenlet.switch()
        

        
    def locked(self):
        return super().locked()


class Semaphore():
    def __init__(self, value=1):
        self.value = value
        self.lock = threading.Lock()
        # scheduler.register_semaphore(self)
        self.queue = []

    def acquire(self, blocking=True, timeout=-1):
        calling_thread=get_calling_thread()
        flag = False
        if scheduler.debug:
            print(f"[semaphone acquire] Semaphore value: {self.value}")
        if blocking:
            if self.value > 0:
                scheduler.state[calling_thread] = ThreadState.IDLE
                self.value -= 1
                flag = True

            else:
                if scheduler.debug:
                    print(f"[Acquire] Semaphore is not available, blocking thread {calling_thread.name}")
                scheduler.state[calling_thread] = ThreadState.BLOCKED
                self.queue.append(calling_thread)
                if calling_thread in scheduler.ready_queue:
                    scheduler.ready_queue.remove(calling_thread)
                
            scheduler.main_greenlet.switch()
            if flag:
                scheduler.state[calling_thread] = ThreadState.RUNNING
                return True
            else:
                self.acquire(blocking, timeout) 
    def release(self):
        if scheduler.debug:
            print(f"[semaphone release] Semaphore value: {self.value}")
        calling_thread=get_calling_thread()
        if self.value == 0:
            for t in self.queue:
                scheduler.state[t] = ThreadState.IDLE
                if t not in scheduler.ready_queue:
                    scheduler.ready_queue.append(t)
        self.value += 1
        scheduler.state[calling_thread] = ThreadState.IDLE
        scheduler.main_greenlet.switch()
        return True
    

class BoundedSemaphore(Semaphore):
    def __init__(self, value=1):
        super().__init__(value)
        self._initial = value


    def release(self):
        if self.value >= self._initial:
            raise ValueError("Semaphore released too many times")
        super().release()

class Condition():
    def __init__(self, lock=None):
        self.lock = lock if lock else RLock()
        self.blocked = []

    def acquire(self, blocking=True, timeout=-1):
        return self.lock.acquire(blocking, timeout)
    def release(self):
        return self.lock.release()
    def wait(self, timeout=None):
        calling_thread = get_calling_thread()
        if calling_thread not in self.blocked:
            self.blocked.append(calling_thread)
        scheduler.state[calling_thread] = ThreadState.BLOCKED
        if calling_thread in scheduler.ready_queue:
            scheduler.ready_queue.remove(calling_thread)
        scheduler.main_greenlet.switch()
        if calling_thread in self.blocked:
            self.wait(timeout)
        else:
            scheduler.state[calling_thread] = ThreadState.RUNNING
            return True
        
    def wait_for(self,predicate,timeout=None):
        calling_thread = get_calling_thread()
        if not predicate():
            if calling_thread not in self.blocked:
                self.blocked.append(calling_thread)
            scheduler.state[calling_thread] = ThreadState.BLOCKED
            if calling_thread in scheduler.ready_queue:
                scheduler.ready_queue.remove(calling_thread)
        else:
            scheduler.state[calling_thread] = ThreadState.IDLE

        scheduler.main_greenlet.switch()
        if not predicate():
            self.wait_for(predicate, timeout)
        else:
            scheduler.state[calling_thread] = ThreadState.RUNNING
            return True
        
    def notify(self, n=1):
        n_threads = min(n, len(self.blocked))
        calling_thread = get_calling_thread()
        scheduler.state[calling_thread] = ThreadState.IDLE
        for _ in range(n_threads):
            thread = self.blocked.pop(0)
            scheduler.state[thread] = ThreadState.IDLE
            if thread not in scheduler.ready_queue:
                scheduler.ready_queue.append(thread)
        scheduler.main_greenlet.switch()
        return True
    
    def notify_all(self):
        n_thread = len(self.blocked)
        self.notify(n_thread)

class Event():
    def __init__(self):
        self._flag = False
    
    def wait(self):
        if self._flag:
            calling_thread = get_calling_thread()
            scheduler.state[calling_thread] = ThreadState.IDLE
        else:
            calling_thread = get_calling_thread()
            scheduler.state[calling_thread] = ThreadState.BLOCKED
            if calling_thread in scheduler.ready_queue:
                scheduler.ready_queue.remove(calling_thread)

        scheduler.main_greenlet.switch()
        if self._flag:
            scheduler.state[calling_thread] = ThreadState.RUNNING
            return True
        else:
            self.wait()
    
    def is_set(self):
        if self._flag:
            return True
        else:
            return False
        
    def clear(self):
        self._flag = False
        calling_thread = get_calling_thread()
        scheduler.state[calling_thread] = ThreadState.IDLE
        scheduler.main_greenlet.switch()
        scheduler.state[calling_thread] = ThreadState.RUNNING
        return True
    def set(self):
        self._flag = True
        calling_thread = get_calling_thread()
        scheduler.state[calling_thread] = ThreadState.IDLE
        scheduler.main_greenlet.switch()
        scheduler.state[calling_thread] = ThreadState.RUNNING
        return True


    

class Barrier():
    def __init__(self, parties,action=None,timeout=None):
        self.parties = parties
        self.action = action
        self.timeout = timeout
        self.blocked = []
        self.aborted = False

    def wait(self):
            
        calling_thread = get_calling_thread()
        scheduler.state[calling_thread] = ThreadState.BLOCKED
        if calling_thread in scheduler.ready_queue:
            scheduler.ready_queue.remove(calling_thread)
        if self.aborted:
            scheduler.main_greenlet.switch()
            scheduler.state[calling_thread] = ThreadState.TERMINATED
            raise RuntimeError(f"Barrier is aborted, thread {calling_thread.name} is terminated")
        id = len(self.blocked)
        self.blocked.append(calling_thread)
        if id == (self.parties-1):
            if self.action:
                self.action()
            while self.blocked:
                thread = self.blocked.pop(0)
                scheduler.state[thread] = ThreadState.IDLE
                if thread not in scheduler.ready_queue:
                    scheduler.ready_queue.append(thread)

        scheduler.main_greenlet.switch()
        scheduler.state[calling_thread] = ThreadState.RUNNING
        return id
    def reset(self):
        self.blocked = []
        calling_thread = get_calling_thread()
        scheduler.state[calling_thread] = ThreadState.IDLE
        if calling_thread not in scheduler.ready_queue:
                scheduler.ready_queue.append(calling_thread)
        scheduler.main_greenlet.switch()
        scheduler.state[calling_thread] = ThreadState.RUNNING
        return True

    def abort(self):
        calling_thread = get_calling_thread()
        scheduler.state[calling_thread] = ThreadState.IDLE
        if calling_thread not in scheduler.ready_queue:
                scheduler.ready_queue.append(calling_thread)
        scheduler.main_greenlet.switch()
        scheduler.state[calling_thread] = ThreadState.RUNNING
        return True
    def parties(self):
        return self.parties
    def n_waiting(self):
        return len(self.blocked)
    def broken(self):
        return self.aborted

        

def new_thread(target, args=()):
    t = ThreadWrapper(target=target, args=args)
    # t.name = f"T-{len(scheduler.threads)+1}"
    return t

def task(id):   
    lock_1.acquire()
    lock_1.acquire()
    time.sleep(1)
    lock_1.release()


def task_special(thread):
    print(f"We will wait for {thread.name}")
    thread.join()
    print(f"Looks like {thread.name} is done")

def task_special2(thread):
    # print(f"Trying to acquire lock_2")
    lock_2.acquire()

    # print(f"Lock acquired,We will wait for {thread.name} to finish")
    thread.join()
    # print(f"Looks like {thread.name} is done, now releasing lock_2")
    lock_2.release()
    # print(f"Lock released")

start_time = time.time()

def get_time():
    return (time.time() - start_time)


scheduler = Scheduler(debug=False)
lock_1 = RLock()
lock_2 = Lock()


# Global variables
m = Lock()
l = Lock()
A = 0
B = 0

def t1():
    global A
    m.acquire()
    A += 1
    if A == 1:
        l.acquire()
    m.release()    
    m.acquire()
    A -= 1
    if A == 0:
        l.release()
    m.release()
    

def t2():
    global B
    m.acquire()
    B += 1
    if B == 1:        
        l.acquire()
    m.release()
    m.acquire()
    B -= 1
    if B == 0:
        l.release()
    m.release()

def t3():
    pass  # Empty function in the original code

def t4():
    pass  # Empty function in the original code

def main():
    # Create threads
    a1 = new_thread(target=t1)
    b1 = new_thread(target=t2)
    a2 = new_thread(target=t3)
    b2 = new_thread(target=t4)
    
    scheduler.register(a1)
    scheduler.register(b1)
    scheduler.register(a2)
    scheduler.register(b2)
    # scheduler.start()

if __name__ == "__main__":


    if __name__ == "__main__":
        if "--verbose" in sys.argv:
            scheduler.verbose()
        if "--interactive" in sys.argv:
            print("Interactive policy selected")
            scheduler.set_policy(0)
        elif "--priority" in sys.argv:
            print("Priority policy selected")
            scheduler.set_policy(2)
        else:
            print("Random policy selected")
            scheduler.set_policy(1)
        if "--benchmark" in sys.argv:
            main()
        else:
            threads = [new_thread(task, args=(i+1,)) for i in range(3)]
            # threads.append(new_thread(task_special2, args=(threads[2],)))
            # threads.append(new_thread(task_special2, args=(threads[3],)))
            for t in threads:
                scheduler.register(t)
    
    scheduler.start()







   
