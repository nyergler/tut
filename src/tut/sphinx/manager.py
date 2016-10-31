
class TutManager(object):

    @classmethod
    def get(cls, env):
        if not hasattr(env, '_tut_mgr'):
            env._tut_mgr = cls()

        return env._tut_mgr

    def __init__(self):
        self.reset()

    def reset(self):
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
        return self.RESET_PATHS
