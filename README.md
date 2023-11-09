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

with SeveranceTest() as test:
    assert test.child_pid() != os.getpid()
```
