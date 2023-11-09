Base Class which on instantiation will spawn a corresponding child in a
sub-process. Methods decorated with `@Severance.control` which are called
on the parent object in the main process will be executed on the child
object in the sub process.

TODO:
 * attributes aren't yet shared between both instances

```python
from severance import Severance
import os

class SeveranceTest(Severance):
    @Severance.control
    def child_pid(self) -> int:
        return os.getpid()


if __name__ == '__main__':
    with SeveranceTest() as test:
        assert test.child_pid() != os.getpid()
```

The following example allows for controlling a pywebview window from a
Python shell:

```python
from severance import Severance
import webview


class GUI(Severance):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self._is_parent:
            self.window = webview.create_window(
                'Woah dude!', html='<h1>Woah dude!<h1>')

    def _run(self, entered=False):
        if not entered:
            webview.start(lambda: self._run(entered=True), debug=True)
            self._is_running.value = False
        else:
            super()._run()

    @Severance.control
    def alert(self, msg):
        self.window.evaluate_js(f'alert("{msg}!")')

    @Severance.control
    def set_h1(self, h1: str):
        self.window.evaluate_js(
            # TODO this probably lacks input sanitation
            f'document.querySelector("h1").textContent = "{h1}"')

    @Severance.control
    def eval_js(self, script):
        self.window.evaluate_js(script)

    @Severance.control
    def quit(self):
        self.window.destroy()
```

In Python shell:

```pycon
>>> gui = GUI()
>>> gui.set_h1("new header")
>>> gui.alert("nice!")
>>> gui.quit()
```
