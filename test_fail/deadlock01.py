# Python translation of the C code provided in benchmark https://github.com/wcventure/PERIOD/blob/main/evaluation/CS/deadlock01/deadlock01_bad.c


# Possible Deadlock

import cosched as threading
from cosched import *
import sys
import time
a = threading.Lock()
b = threading.Lock()
counter = 1

def thread1():
    global counter
    a.acquire()
    b.acquire()
    counter += 1
    b.release()
    a.release()

def thread2():
    global counter
    b.acquire()
    a.acquire()
    counter -= 1
    a.release()
    b.release()

def join_thread(t1, t2):
    t1.join()
    t2.join()

def main():
    t1 = threading.Thread(target=thread1)
    t2 = threading.Thread(target=thread2)
    
    t1.start()
    t2.start()

    t3 = threading.Thread(target=join_thread, args=(t1, t2))
    

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
    
    main()
    
    cosched_start()