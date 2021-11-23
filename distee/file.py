
import io


class File:

    def __init__(self, fp: 'io.BufferedIOBase', name: str, description: str):
        self.fp: 'io.BufferedIOBase' = fp
        self.filename = name
        self.spoiler: bool = False
        self.description = description
        self._original_pos = fp.tell()

    def reset(self, seek=True):
        if seek:
            self.fp.seek(self._original_pos)
