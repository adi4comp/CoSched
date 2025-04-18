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
        self.debug = debug    
        self.greenlets = {} 
        self.policy = 1
        self.main_greenlet = greenlet(self._scheduler_loop)
        self.schedule = []
        self.thread_priority = {}
        self.locks = []
        self.rlocks = []
        self.semaphores = []
        self.condition = []
        self.barriers = []
        self.events = []
        self.error = 0

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

        # error = []
        # for t in self.threads:
        #     if self.state[t] != ThreadState.TERMINATED:
        #         error.append(t)

        print("\n\n-------[Scheduler Summary] All threads have finished execution-------\n")
        try:
            self.check_resource_starvation()
            self.check_deadlock()
        except RuntimeError as e:
            print(e)
        
        print(f"\n[Scheduler Schedule] Scheduled Picked This time: {'-> '.join([t.name for t in self.schedule])}\n")
        if self.error > 0:
            print(f"\n[Scheduler Summary] There is/are {self.error} error in the above interleaving\n")

        print("\n-------------[Scheduler Summary] End of Scheduler Summary------------")
    def check_resource_starvation(self):
        for l in self.locks:
            if l.locked == True:
                if(self.state[l.lock_holder] == ThreadState.TERMINATED):
                    error = []
                    for x in self.queue:
                        if self.state[x] != ThreadState.TERMINATED:
                            error.append(x)
                    if error:
                        self.error += 1
                        raise RuntimeError(f"\nError {self.error}: [Resource Starvation]<Lock> Thread {l.lock_holder.name} is terminated and didn't release the lock which starved {', '.join([t.name for t in error])}\n")
        for s in self.semaphores:
            if s.value == 0:
                error = []
                for x in s.queue:
                    if self.state[x] != ThreadState.TERMINATED:
                        error.append(x)
                if error:
                    self.error += 1
                    raise RuntimeError(f"\nError {self.error}: [Resource Starvation] <Semaphore> Threads {', '.join([t.name for t in error])} starved for Semaphore {self.semaphores.index(s)}\n")
        for r in self.rlocks:
            if r.locked == True:
                if (self.state[r.lock_holder] == ThreadState.TERMINATED):
                    error = []
                    for x in r.queue:
                        if self.state[x] != ThreadState.TERMINATED:
                            error.append(x)
                    if error:
                        self.error += 1
                        raise RuntimeError(f"\nError {self.error}: [Resource Starvation] <RLock> {r.lock_holder} is terminated and didn't release the lock ({r.rlock_counter} times) which starved {', '.join([t.name for t in error])} threads\n")
        for c in self.condition:
            if c.lock.locked == True:
                if (self.state[c.lock.lock_holder] == ThreadState.TERMINATED):
                    error = []
                    for x in c.blocked:
                        if self.state[x] != ThreadState.TERMINATED:
                            error.append(x)
                    if error:
                        self.error += 1
                        raise RuntimeError(f"\nError {self.error}: [Resource Starvation] Thread {c.lock.lock_holder} is terminated and didn't release the condition lock which starved {', '.join([t.name for t in error])} \n")
        for b in self.barriers:
            if b.blocked and b.aborted == False:
                    error = []
                    for x in b.blocked:
                        if self.state[x] != ThreadState.TERMINATED:
                            error.append(x)
                    if error:
                        self.error += 1
                        raise RuntimeError(f"\nError {self.error}: [Resource Starvation] Barrier {b} couldnt be unblocked which starved {', '.join([t.name for t in error])} \n")
            
        for e in self.events:
            if e._flag == False:
                error = []
                for x in e.blocked:
                    if self.state[x] != ThreadState.TERMINATED:
                        error.append(x)
                if error:
                    self.error += 1
                    raise RuntimeError(f"\nError {self.error}: [Resource Starvation] Event {e} didn't happen which starved {', '.join([t.name for t in error])} threads")

    def check_deadlock(self):
        deadlock_dependency_tree = {}
        for t in self.threads:
            deadlock_dependency_tree[t] = None
            if self.state[t] == ThreadState.BLOCKED:
                for l in self.locks:
                    if t in l.queue:
                        if self.state[l.lock_holder] == ThreadState.BLOCKED:
                            deadlock_dependency_tree[t] = l.lock_holder
                if deadlock_dependency_tree[t] == None:
                    for r in self.rlocks:
                        if t in r.queue:
                            if self.state[r.lock_holder] == ThreadState.BLOCKED:
                                deadlock_dependency_tree[t] = r.lock_holder
                if deadlock_dependency_tree[t] == None:
                    for c in self.condition:
                        if t in c.blocked:
                            if self.state[c.lock.lock_holder] == ThreadState.BLOCKED:
                                deadlock_dependency_tree[t] = c.lock.lock_holder
                if deadlock_dependency_tree[t] == None:
                    for s in scheduler.threads:
                        if t in s.wait_join:
                            if self.state[s] == ThreadState.BLOCKED:
                                deadlock_dependency_tree[t] = s


        flag = False
        for t in self.threads:
            if deadlock_dependency_tree[t] != None:
                flag = True 
                break
        
        if flag:
            self.error += 1
            print("\nError {}: [Deadlock] Deadlock Detected:".format(self.error))
            for parent, child in deadlock_dependency_tree.items():
                if parent!= None and child != None:
                    print(f"{parent.name} -> {child.name}")

    
                                                    
                
                        
            

        
    def register(self, thread):
        self.threads.append(thread)
        if thread not in self.ready_queue:
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
                    self.error += 1
                    print(f"[ERROR] Exception in thread {thread.name}: {e}")
                finally:
                    if self.debug:
                        print(f"[Greenlet] Thread {thread.name} completed execution")
                    self.state[thread] = ThreadState.TERMINATED
                    if thread.wait_join:
                        for x in thread.wait_join:
                            self.state[x] = ThreadState.IDLE
                            if x not in self.ready_queue:
                                self.ready_queue.append(x)
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



scheduler = Scheduler(debug=False)

def get_time():
    return time.time()

def cosched_set_policy(policy):
    if policy in [0, 1, 2]:
        scheduler.set_policy(policy)
    else:
        raise ValueError("Invalid policy. Choose 0 (manual), 1 (random), or 2 (priority).")
    
def cosched_set_verbose():
    scheduler.verbose()



def get_calling_thread():
    for t in scheduler.threads:
        if scheduler.state[t] == ThreadState.RUNNING:
            return t
    if scheduler.debug:
        print("No calling thread found")
        print(f"Scheduler state: {scheduler.state}")
    return None


class Thread(threading.Thread):
    def __init__(self, target=None, args=()):
        super().__init__(target=target, args=args)
        scheduler.register(self)
        self._preserve_target = self._target
        self._preserve_args = self._args
        self._preserve_kwargs = self._kwargs
        self.wait_join = []
    def start(self):
        if scheduler.debug:
            print(f"Thread is queued for execution :{self.name}")
        pass
        
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
        if scheduler.debug:
            print(f"[Join] Preempting Thread {calling_thread.name} for {self.name} to finish")
        if scheduler.state[self] != ThreadState.TERMINATED:
            self.wait_join.append(calling_thread)
            scheduler.state[calling_thread] = ThreadState.BLOCKED
            if calling_thread in scheduler.ready_queue:
                scheduler.ready_queue.remove(calling_thread)
            scheduler.main_greenlet.switch()
            

        else:
            if scheduler.debug:
                print(f"[Join] Thread {calling_thread.name} resumed after {self.name} completion")
            for t in self.wait_join:
                scheduler.state[t] = ThreadState.IDLE
                if t not in scheduler.ready_queue:
                    scheduler.ready_queue.append(t)
            scheduler.main_greenlet.switch()

        return True
                
        
        
            


class Lock():
    def __init__(self):
        self.locked = False
        scheduler.locks.append(self)
        self.queue = []
        self.lock_holder = None
        
    def acquire(self, blocking=True, timeout=-1):
        if blocking:
            if not self.locked and self.lock_holder == None:
                self.locked = True
                self.lock_holder = get_calling_thread()
                scheduler.state[get_calling_thread()] = ThreadState.IDLE
                scheduler.main_greenlet.switch()
                return True
            else:
                if scheduler.debug:
                    print(f"[Acquire] Lock is already held by {self.lock_holder}")
                calling_thread = get_calling_thread()
                scheduler.state[calling_thread] = ThreadState.BLOCKED
                if calling_thread in scheduler.ready_queue:
                    scheduler.ready_queue.remove(calling_thread)
                    
                holder_thread = self.lock_holder
                if scheduler.state[holder_thread] == ThreadState.TERMINATED:
                    scheduler.state[calling_thread] = ThreadState.BLOCKED
                    self.queue.append(calling_thread)
                    if calling_thread in scheduler.ready_queue:
                        scheduler.ready_queue.remove(calling_thread)
                    scheduler.main_greenlet.switch()
                
                if calling_thread not in self.queue:
                    self.queue.append(calling_thread)
                scheduler.main_greenlet.switch()
                self.acquire(blocking, timeout)
                
        else:
            if not self.locked and self.lock_holder == None:
                self.locked = True
                self.lock_holder = get_calling_thread()
                scheduler.main_greenlet.switch()
                return True
            else:
                scheduler.main_greenlet.switch()
                return False
                
    def release(self):
        calling_thread = get_calling_thread()
        if self.locked and self.lock_holder == get_calling_thread():
            self.locked = False
            self.lock_holder = None
            scheduler.state[calling_thread] = ThreadState.IDLE
            if calling_thread not in scheduler.ready_queue:
                scheduler.ready_queue.append(calling_thread)
            if self.queue:
                next_thread = self.queue.pop(0)
                scheduler.state[next_thread] = ThreadState.IDLE
                if next_thread not in scheduler.ready_queue:
                    scheduler.ready_queue.append(next_thread)
                if scheduler.debug:
                    print(f"[Release] Lock released by {calling_thread.name}, waking up {next_thread.name}")
            else:
                if scheduler.debug:
                    print(f"[Release] Lock released by {calling_thread.name}, no threads waiting")

        elif self.locked and self.lock_holder != get_calling_thread():
            scheduler.state[get_calling_thread] = ThreadState.TERMINATED
            raise RuntimeError(f"Cannot release a lock that is not held (held by {self.lock_holder}) by the calling thread {calling_thread.name}")
        
        elif not self.locked:
            scheduler.state[get_calling_thread] = ThreadState.TERMINATED
            raise RuntimeError(f"Cannot release an unlocked lock {calling_thread.name} ")
        
        scheduler.main_greenlet.switch()
               
    def locked(self):
        if self.locked:
            return True
        else:   
            return False
            
    def __enter__(self):
        self.acquire()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


class RLock(Lock):
    def __init__(self):
        super().__init__()
        self.rlock_counter = 0
        scheduler.rlocks.append(self)
        if self in scheduler.locks:
            scheduler.locks.remove(self)
    def acquire(self, blocking=True, timeout=-1):
        if self.rlock_counter==0:
            self.rlock_counter = 1
            return super().acquire(blocking, timeout)
        if self.locked and self.lock_holder == get_calling_thread():
            self.rlock_counter += 1
            calling_thread = get_calling_thread()
            scheduler.state[calling_thread] = ThreadState.IDLE
            scheduler.main_greenlet.switch()
            return True
        else:
            return super().acquire(blocking, timeout)
            
            
    def release(self):
        if self.locked and self.lock_holder == get_calling_thread():
            self.rlock_counter -= 1
            if self.rlock_counter == 0:
                super().release()
        else:
            raise RuntimeError(f"Cannot release a lock that is not held (held by {self.lock_holder}) by the calling thread {get_calling_thread().name}")
        scheduler.main_greenlet.switch()
        

        
    def locked(self):
        return super().locked()


class Semaphore():
    def __init__(self, value=1):
        self.value = value
        # scheduler.register_semaphore(self)
        self.queue = []
        scheduler.semaphores.append(self)

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
                if calling_thread not in self.queue:
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
    
    # Add context manager support
    def __enter__(self):
        self.acquire()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

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
        scheduler.condition.append(self)
        if self.lock in scheduler.locks:
            scheduler.locks.remove(self.lock)
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
        
    def __enter__(self):
        self.acquire()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

class Event():
    def __init__(self):
        self._flag = False
        scheduler.events.append(self)

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
        scheduler.barriers.append(self)

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


def cosched_start():
    scheduler.start()


__all__ = [
    'Thread', 'Lock', 'RLock', 'Semaphore', 'BoundedSemaphore',
    'Condition', 'Event', 'Barrier', 'cosched_set_policy', 'cosched_set_verbose', 'cosched_start'
]
