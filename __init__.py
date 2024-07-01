import pkgutil, importlib
from accelerators import Accelerator

for _, module, _ in pkgutil.iter_modules(__path__):
    importlib.import_module(f"{__name__}.{module}")

def register_subclasses(cls):
    subclasses = cls.__subclasses__()
    if not len(subclasses):
        globals()[cls.__name__] = cls
    else:
        for subclass in subclasses:
            register_subclasses(subclass)

register_subclasses(Accelerator)
