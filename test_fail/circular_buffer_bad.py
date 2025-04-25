
# Python translation of the C code benchmark https://github.com/wcventure/PERIOD/blob/main/evaluation/CS/account/account_bad.c

## Possible Data Race : assertion fails in thread 2

import cosched as threading
from cosched import *
import sys
import time


BUFFER_MAX = 10
N = 7
ERROR = -1
FALSE = 0
TRUE = 1


buffer = [0] * BUFFER_MAX    
first = 0                    
next_ptr = 0                 
buffer_size = 0              
send = False
receive = False
m = threading.Lock()

def initLog(max_size):
    global buffer_size, first, next_ptr
    buffer_size = max_size
    first = next_ptr = 0

def removeLogElement():
    global first
    assert first >= 0
    if next_ptr > 0 and first < buffer_size:
        result = buffer[first]
        first += 1
        return result
    else:
        return ERROR

def insertLogElement(b):
    global next_ptr
    if next_ptr < buffer_size and buffer_size > 0:
        buffer[next_ptr] = b
        next_ptr = (next_ptr + 1) % buffer_size
        assert next_ptr < buffer_size
    else:
        return ERROR
    return b

def t1():
    global send, receive
    for i in range(N):
        with m:
            if send:
                insertLogElement(i)
                send = FALSE
                receive = TRUE

def t2():
    global send, receive
    for i in range(N):
        with m:
            if receive:
                assert removeLogElement() == i, f"index {i} not found in buffer"
                receive = FALSE
                send = TRUE

def join_thread(t1, t2):
    t1.join()
    t2.join()
    

def main():
    global send, receive
    
    initLog(10)
    send = TRUE
    receive = FALSE
    

    thread1 = threading.Thread(target=t1)
    thread2 = threading.Thread(target=t2)
    

    thread1.start()
    thread2.start()

    thread3 = threading.Thread(target=join_thread, args=(thread1, thread2))


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
    start = time.perf_counter()
    cosched_start()
    end = time.perf_counter()
    print(f"Execution time: {(end - start) * 1000000:.4f} microseconds")