## Serial Schedulizer for Python


Goal to create a custom scheduler to do controlled concurrency testing, Instructions given by Dylan:

1. Create a python library with same API as python threading Module

2. Use global mutex to run one thread at a time

3. Track data for which threads are alive or blocked

4. Delegate most of the other implementations to the threading module

5. Start with a simple program that creates some threads and exits

## Sketch for the solution

Scheduler instance initially contains these states:
- threads: list of threads that are ready to be executed
- current_thread: the thread that is currently being executed
- state: the state of each thread (waiting,running, dead, sync (thread id waiting for sync)) (maybe instead of map a list belonging to each of this category)
- lock: thread holding the lock currently


### Thread Instantiation:
- currently no change needed to this function


### Thread.start():
- Add the threads to the scheduler's threads list (register the thread with the scheduler)

### Thread.run():
- Change the state of the thread to running

### Thread.join():
- Change the state of the calling thread to sync(thread_id of the `Thread` it is waiting for)

###  Thread.lock.acquire():
- check if any of the waiting/sync threads are holding the lock
- if yes:
    - change the state of the calling thread to waiting
    - add the calling thread to the waiting list of the lock
- else:
    - add thread to lock id
    - resume the thread to running state

### Thread.lock.release():
- remove the thread from the lock state and continue execution of the same thread
- if the lock state is empty raise a runtime error


