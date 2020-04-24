__author__ = 'quentin'

import cv2
import unittest
import os
import pickle
import datetime
import time
import sys

from ethoscope.roi_builders.target_roi_builder import FSLSleepMonitorWithTargetROIBuilder, SleepMonitorWithTargetROIBuilder, TargetGridROIBuilder
print(os.getcwd())

try:
    from cv2.cv import CV_AA as LINE_AA
except ImportError:
    from cv2 import LINE_AA

images = {
           "test_qc": "../static_files/img/dark_targets_above.png",
           "test_light": "../static_files/img/light.png"}


LOG_DIR = "./test_logs/"

class TestTargetROIBuilder(unittest.TestCase):

    roi_builder = SleepMonitorWithTargetROIBuilder()
    
    
    def setUp(self):
        
        self.class_name = self.__class__.__name__
        print(self.class_name)


    def _draw(self,img, rois):
        for r in rois:
            cv2.drawContours(img,r.polygon,-1, (255,255,0), 2, LINE_AA)


    def _test_one_img(self,path=None, out=None):
        
        try:
            import picamera
            with picamera.PiCamera() as cam:
                now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%s")
                dst = os.path.join(LOG_DIR, f'{now}.png')
                time.sleep(1)
                cam.capture(dst)
            img = cv2.imread(dst)
        except ImportError:
            img = cv2.imread(path)

        rois = self.roi_builder.build(img)
        pickle_file = os.path.join(LOG_DIR, self.class_name + "_rois.pickle")
        with open(pickle_file, "wb") as fh:
            pickle.dump(rois, fh)
        self._draw(img, rois)
        if out is None:
            out = os.path.join(LOG_DIR, f'{now}_annot.png')
        cv2.imwrite(out,img)
        cv2.imwrite(f'/tmp/rois_{self.message}.png',img)
        self.assertEqual(len(rois),20)


    def test_all(self):

        for k,i in list(images.items()):
            out = os.path.join(LOG_DIR,self.class_name +".png")
            print(out)
            self._test_one_img(i,out)


class TestFSLROIBuilder(TestTargetROIBuilder):

    roi_builder = FSLSleepMonitorWithTargetROIBuilder()




if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('-m', '--message', help='Message is written to the output file as a suffix')
    args = vars(ap.parse_args())
    print(args)
    message = args['message']
    TestFSLROIBuilder.message = message
    test_instance = TestFSLROIBuilder()
    test_instance.setUp()
    test_instance._test_one_img()

    

