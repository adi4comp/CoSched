import sys
import cosched as threading
from cosched import *
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
    pass  

def t4():
    pass

def main():
    a1 = Thread(target=t1,args=())
    b1 = Thread(target=t2,args=())
    a2 = Thread(target=t3,args=())
    b2 = Thread(target=t4,args=())

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
    
    main()
    cosched_start()