import cosched as threading
from cosched import *

import time
import sys




def new_thread(target, args=()):
    t = Thread(target=target, args=args)
    return t

def task(id):   
    rlock_1.acquire()
    print(f"Thread {id} acquired lock 1 times")
    rlock_1.acquire()
    print(f"Thread {id} acquired lock 2 times")
    time.sleep(1)
    print(f"Thread {id} releasing lock 1 times")
    rlock_1.release()
    print(f"Thread {id} is terminating")


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

rlock_1 = RLock()
# lock_2 = Lock()


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
    
    # scheduler.register(a1)
    # scheduler.register(b1)
    # scheduler.register(a2)
    # scheduler.register(b2)
    # scheduler.start()

if __name__ == "__main__":


    if __name__ == "__main__":
        if "--verbose" in sys.argv:
            set_verbose()
        if "--interactive" in sys.argv:
            print("Interactive policy selected")
            set_policy(0)
        elif "--priority" in sys.argv:
            print("Priority policy selected")
            set_policy(2)
        else:
            print("Random policy selected")
            set_policy(1)
        if "--benchmark" in sys.argv:
            main()
        else:
            threads = [new_thread(task, args=(i+1,)) for i in range(3)]
            # threads.append(new_thread(task_special2, args=(threads[2],)))
            # threads.append(new_thread(task_special2, args=(threads[3],)))
    
    cosched_start()