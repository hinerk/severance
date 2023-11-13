from typing import Callable
from multiprocessing import Pipe, Process, Value
from multiprocessing.connection import Connection
from abc import ABC


class Severance(ABC):
    """
    Base Class which on instantiation will spawn a corresponding child in a
    sub-process. Methods decorated with @Severance.control which are called
    on the parent object in the main process will be executed on the child
    object in the sub process.

    TODO:
     * attributes aren't yet shared between both instances

    ```python
    class SeveranceTest(Severance):
        @Severance.control
        def child_pid(self) -> int:
            return os.getpid()

    test = SeveranceTest()
    print(f"child PID: {test.child_pid()}")
    print(f'main: {os.getpid()}')
    test.join()
    ```
    """
    def __init__(
            self,
            poll_timeout: float = 0.001,
            _conn: Connection = None,
            _is_running: Value = None,
            _is_parent: bool = True):
        """
        :param poll_timeout: timeout for receiving data on the connecting pipe
        :param _conn: Private: do not touch!
        one end of multiproccessing.Pipe()
        :param _is_running: Private: do not touch!
        whether child event loop is running
        :param _is_parent: Private: do not touch!
        whether to instantiate a child or a parent
        """
        self._poll_timeout = poll_timeout
        self._conn = _conn
        self._is_running = _is_running
        self._is_parent = _is_parent

        if not _is_parent:
            return

        self._conn, child_conn = Pipe()
        self._is_running = Value('b', False)
        self._child_process = Process(
            target=self._create_child_process,
            kwargs=dict(
                poll_timeout=poll_timeout,
                conn=child_conn,
                is_running=self._is_running))
        self._child_process.start()

    def __getstate__(self):
        __dict__ = self.__dict__.copy()
        __dict__['_child_process'] = None
        return __dict__

    @classmethod
    def _create_child_process(
            cls, poll_timeout: float, conn: Connection, is_running: Value):
        """is called to spawn child in sub process"""
        child = cls(poll_timeout=poll_timeout, _conn=conn,
                    _is_running=is_running, _is_parent=False)
        child._run()

    @classmethod
    def control(cls, func: Callable):
        """decorates a method which shall be called on the child process"""
        def wrapper(self: cls, *args, **kwargs):
            if self._is_parent:
                self._conn.send((func.__name__, args, kwargs))
                return self._conn.recv()
            else:
                return func(self, *args, **kwargs)
        return wrapper

    def _run(self):
        """event loop of the child process"""
        self._is_running.value = True
        while self._is_running.value:
            if not self._conn.poll(self._poll_timeout):
                continue
            func_name, args, kwargs = self._conn.recv()
            assert hasattr(self, func_name)
            returned = getattr(self, func_name)(*args, **kwargs)
            self._conn.send(returned)

    def join(self, timeout: float = None):
        """terminate the child's event loop and join process"""
        if not self._is_parent:
            raise RuntimeError(
                "join() shall not be called in the child process!")
        if self._child_process is None:
            # if not a child and _child_process is None, this instance likely
            # is a copy
            return
        self._is_running.value = False
        self._child_process.join(timeout)

    def __del__(self):
        if self._is_parent:
            self.join()
        else:
            self._is_running.value = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.join()
