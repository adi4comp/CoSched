# Possible Deadlock
# import cosched as threading
# from cosched import *
import threading
from threading import *
import time
import sys

lock_1 = Lock()
def task(i):
    pass

def task_2(thread):
    lock_1.acquire()
    thread.join()

if __name__ == "__main__":
    # if "--verbose" in sys.argv:
    #     cosched_set_verbose()
    # if "--interactive" in sys.argv:
    #     print("Interactive policy selected")
    #     cosched_set_policy(0)
    # elif "--priority" in sys.argv:
    #     print("Priority policy selected")
    #     cosched_set_policy(2)
    # else:
    #     print("Random policy selected")
    #     cosched_set_policy(1)
    
    start = time.perf_counter()
    threads = [Thread(target=task, args=(i+1,)) for i in range(2)]
    threads.append(Thread(target=task_2, args=(threads[0],)))
    threads.append(Thread(target=task_2, args=(threads[2],)))
    
    
    # cosched_start()
    end = time.perf_counter()
    print(f"Execution time: {(end - start) * 1000000:.4f} microseconds")