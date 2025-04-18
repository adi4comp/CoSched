# Resource Starvation
import sys
import cosched as threading
from cosched import *
import time


rlock_1 = RLock()

def task(id):   
    rlock_1.acquire()
    print(f"Thread {id} acquired lock 1 times")
    rlock_1.acquire()
    print(f"Thread {id} acquired lock 2 times")
    time.sleep(1)
    print(f"Thread {id} releasing lock 1 times")
    rlock_1.release()
    print(f"Thread {id} is terminating")



if __name__ == "__main__":
    if "--verbose" in sys.argv:
        cosched_set_verbose()
    if "--interactive" in sys.argv:
        print("Interactive policy selected")
        cosched_set_policy(0)
    elif "--priority" in sys.argv:
        print("Priority policy selected")
        cosched_set_policy(2)
    else:
        print("Random policy selected")
        cosched_set_policy(1)
    
    
    threads = [Thread(target=task, args=(i+1,)) for i in range(3)]
    
    cosched_start()


    


