from tut.model import Tut


class UNSET(object):
    pass
UNSET = UNSET()


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
        self._options = {}

        self.DEFAULT_PATH = None
        self.RESET_PATHS = {}

    @property
    def reset_paths(self):
        return {
            t: path
            for t, path in self.tuts.items()
        }

    def tut(self, path):
        """Return a Tut for the given path."""
        if path not in self.tuts:
            self.tuts[path] = Tut(path)

        return self.tuts[path]

    def reset_tuts(self):
        for tut in self.tuts.values():
            tut.reset()

    def update_defaults(self, options):

        self._options = options.copy()

    def resolve_option(self, node, key, default=UNSET):

        if key in node.options:
            return node.options[key]

        if key in self._options:
            return self._options[key]

        if default is not UNSET:
            return default

        raise Exception("No tut {0} specified.".format(key))

    def __getattr__(self, key):
        if key.startswith('default_') and key.split('_', 1)[-1] in self._options:
            return self._options[key.split('_', 1)[-1]]

        return super(TutManager, self).__getattr__(key)