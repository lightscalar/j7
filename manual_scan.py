import sys
sys.path.append('../mathtools')
from mathtools.utils import Vessel


if __name__ == '__main__':

    v = Vessel('request.oracle')
    v.scan = {'_id': '12354'}
    v.save()
