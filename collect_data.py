from gazepoint import GazePoint
import sys
sys.path.append('../../mathtools')
from mathtools.utils import Vessel


if __name__ == '__main__':
    
    scan = {'_id': '12342134'}
    gazepoint = GazePoint()
    data = gazepoint.collect(scan)
    gazepoint.kill()


 
