import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clientradar.ui.app import ClientRadarApp

if __name__ == "__main__":
    ClientRadarApp().run()
