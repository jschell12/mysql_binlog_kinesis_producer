class Utils(object):
    @staticmethod
    def dump(obj):
        for attr in dir(obj):
            print("obj.%s = %r" % (attr, getattr(obj, attr)), flush=True)


