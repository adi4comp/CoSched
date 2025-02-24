## Serial Schedulizer for Python


Goal to create a custom scheduler to do controlled concurrency testing, Instructions given by Dylan:

1. Create a python library with same API as python threading Module

2. Use global mutex to run one thread at a time

3. Track data for which threads are alive or blocked

4. Delegate most of the other implementations to the threading module

5. Start with a simple program that creates some threads and exits

