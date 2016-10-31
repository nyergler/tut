from tut.model import Tut


class TutManager(object):

    @classmethod
    def get(cls, env):
        if not hasattr(env, '_tut_mgr'):
            env._tut_mgr = cls()

        return env._tut_mgr

    def __init__(self):
        self.reset()

    def reset(self):
        self.tuts = {}

        self.DEFAULT_PATH = None
        self.RESET_PATHS = {}

    @property
    def default_path(self):
        return self.DEFAULT_PATH

    @default_path.setter
    def default_path(self, path):
        self.DEFAULT_PATH = path

    @property
    def reset_paths(self):
        return {
            t: path
            for t, path in self.tuts.items()
        }
        return self.RESET_PATHS

    def tut(self, path):
        """Return a Tut for the given path."""
        if path not in self.tuts:
            self.tuts[path] = Tut(path)

        return self.tuts[path]

    def reset_tuts(self):
        for tut in self.tuts.values():
            tut.reset()
