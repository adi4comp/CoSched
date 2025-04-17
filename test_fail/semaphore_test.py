import cosched as threading
from cosched import *
import time
import sys


s1 = Semaphore(0)

def task(id):
    s1.acquire()

def task_2(id):
    s1.release()




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
    threads.append(Thread(target=task_2, args=(4,)))
    
    cosched_start()