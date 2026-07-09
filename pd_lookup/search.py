import os
import re

path = os.path.abspath(__file__)
dir_path = os.path.dirname(path)

class PersonalDevice(object):

    def __init__(self):
        self.cache = {}
        self.patterns = []
        self.mtimes = {}
        self._load_patterns()

    def _load_patterns(self):
        self.patterns = []
        self.mtimes = {}
        txt_dir = "{}/txt".format(dir_path)
        sorted_files = sorted(os.scandir(txt_dir), key=lambda e: e.name)
        for filename in sorted_files:
            if filename.is_file():
                self.mtimes[filename.path] = filename.stat().st_mtime
                _, devicetype = filename.name.split('_', 1)
                with open(filename.path) as f:
                    for line in f:
                        pattern = line.rstrip()
                        if pattern:
                            self.patterns.append(
                                (re.compile(pattern, re.IGNORECASE), pattern.lower(), devicetype)
                            )

    def reload_if_changed(self):
        txt_dir = "{}/txt".format(dir_path)
        try:
            current = {e.path: e.stat().st_mtime for e in os.scandir(txt_dir) if e.is_file()}
        except OSError:
            return False
        if current != self.mtimes:
            self.cache.clear()
            self._load_patterns()
            return True
        return False

    def search(self, *args) -> list:
        for txt in args:
            if txt in self.cache:
                return self.cache[txt]
            for compiled, pattern_str, devicetype in self.patterns:
                if compiled.search(txt):
                    result = [devicetype, pattern_str]
                    self.cache[txt] = result
                    return result
        return ["", ""]

    def getPatterns(self) -> list:
        return self.patterns
