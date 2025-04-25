# Python translation of the C code benchmark https://github.com/wcventure/PERIOD/blob/main/evaluation/CS/account/account_bad.c

# Possible Data race : assertion fails

import cosched as threading
from cosched import *
import sys
import time


m = Lock()
x, y, z, balance = 0, 0, 0, 0
deposit_done = False
withdraw_done = False

def deposit():
    global balance, deposit_done
    with m:
        balance = balance + y
        deposit_done = True

def withdraw():
    global balance, withdraw_done
    with m:
        balance = balance - z
        withdraw_done = True

def check_result():
    global balance, deposit_done, withdraw_done
    with m:
        if deposit_done and withdraw_done:
            assert balance == (x - y) - z, "Balance check failed" 

def join_thread(t1, t2, t3):
    
    
    t2.join()
    t1.join()
    t3.join()


def main():
    global x, y, z, balance
    
    
    x = 1
    y = 2
    z = 4
    balance = x
    
    
    t1 = Thread(target=deposit)
    t2 = Thread(target=withdraw)
    t3 = Thread(target=check_result)

    t3.start()
    t1.start()
    t2.start()

    t4 = Thread(target=join_thread, args=(t1, t2, t3))
    t4.start()
    



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