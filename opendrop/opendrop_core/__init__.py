from opendrop.constants import OperationMode

from opendrop.opendrop_core import ift
from opendrop.opendrop_core import conan

def main(mode, conf):
    if mode == OperationMode.PENDANT or mode == OperationMode.SESSILE:
        return ift.calculate(mode, conf)
    elif mode == OperationMode.CONAN or mode == OperationMode.CONAN_NEEDLE:
        return conan.calculate(mode, conf)

if __name__ == '__main__':
    raise NotImplementedError("Cannot be directly run")
