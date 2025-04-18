# CoSched: Schedule Serializer for Python Threads


**Goal**: To create a custom scheduler to do controlled concurrency testing of Python threading programs.


## Getting Started

1. To do the env setup  all u need is python and greenlet library. However u can use the `setup.sh` script to automate this.

```bash
bash setup.sh -form <local/docker> #default local
```

local will create a virtualenv and install the dependencies in it. Docker will create a docker image with the dependencies installed in it and launch the terminal.

2. To run the tests, you can use the `tests.sh` script this will run the failing tests in [`test_fail`](test_fail/)

```bash
bash tests.sh -policy <name> -iter <number>
```

This will run the policy with the given number of iterations. The default policy is `random` and the default number of iterations is 1. Currently the policies available are:
- `random`: Randomly select a thread to run
- `priority`: Select the thread that just ran with least priority, and all others with random choice
- `interactive`: Select the thread interactively (useful for debugging)

The summary of the results for the tests are displayed on the `stdout` and the detailed logs are saved in the `logs` directory of test directory.

3. To use the `CoSched` as library, add the src directory to Python path. You can do this by running the following command in your terminal from the root of this repository:

```bash
export PYTHONPATH=$(pwd)/src:$PYTHONPATH
```

Then u can use the library by just using this standard wrapper around the normal threading library code.

```python
import cosched as threading
from cosched import *

# Application code

if __name__ == "__main__":
    # optionally set the policy random/priority/interactive
    # 0: interactive 1: random 2: priority  (Default: 1)
    # cosched_set_policy(1)
    # for verbose output
    # cosched_set_verbose()
    cosched_start()

```

## Brief Description

The goal of this tool is to create a custom scheduler for controlled concurrency testing using Python's threading module. While most of the the python interpreters manage the thread execution with GIL, this tool is useful in generating interleavings in possible logical concurrency errors such as resource starvation, deadlock and a small subset of data races.


The tool uses coroutines to simulate thread preemption (therefore the name) (delegated to the greenlet library) a parent class `Scheduler` is used to store thread and synchronization primitives of threads. Most of the components and primitives of the `threading` library has been wrapped into the current implementation (With some potential Bugs :( ). Some primitives such as timeouts have been left because in controlled concurrency testing timeout may not be so useful (intution).


## Information on Tests

A. The scheduler can detect deadlocks for eg:

1. [benchmark_carter_c01.py](test_fail/benchmark_carter_c01.py)
2.  [deadlock01.py](test_fail/deadlock01.py)
3. [wait_join.py](test_fail/wait_join.py)

B. The scheduler can also detect resource starvation for eg:

1. [rlock_test.py](test_fail/rlock_test.py)
2. [semaphore_test.py](test_fail/semaphore_test.py)


C. The scheduler can detect logical data races (checked using assertions) for eg:

1. [account_bad.py](test_fail/account_bad.py)
2. [circular_buffer.py](test_fail/circular_buffer.py)

**Note:** Data races is a very broad condition which mainly happens on the low level of the code. Since python is a high level language and has a runtime interpreter, it is very difficult to examine the low level data, therefore the subset of data races is only logical data race where global states are mutated by multiple threads and may lead to inconsistent states.


## Acknowledgements
This tool is part of the course project CS6215 "Advanced Topics in Program Analysis". The idea is provided by the Project Mentors of the course Dylan Wolf and Zhao Huan.


