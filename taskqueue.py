from threading import Thread
import queue
import time

class TaskQueue(queue.Queue):

    def __init__(self):
        queue.Queue.__init__(self)
        self.thread = Thread(target=self.worker)
        self.thread.daemon = True
        self.thread.start()

    def add_task(self, task, *args, **kwargs):
        args = args or ()
        kwargs = kwargs or {}
        self.put((task, args, kwargs))

    def worker(self):
        while True:
            task, args, kwargs = self.get()
            task(*args, **kwargs)
            self.task_done()

    def __len__(self):
        return len(self.queue)


if __name__ == "__main__":
    q = TaskQueue()

    def atask(number=0):
        time.sleep(1)
        print(f"A task {number} finished. Still {len(q)} tasks to do")

    for i in range(10):
        q.add_task(atask, i)

    q.join()
    print("All done!")