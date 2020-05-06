__author__ = 'quentin'

import numpy as np

import logging
import traceback
import cv2
import os

from ethoscope.utils.description import DescribedObject
from ethoscope.core.roi import ROI


class BaseROIBuilder(DescribedObject):

    _target_coord_file = "/etc/target_coordinates.conf"

    def __init__(self, target_coordinates_file):
        """
        Template to design ROIBuilders. Subclasses must implement a ``_rois_from_img`` method.
        """

        if "target_coordinates_file" is not None:
            self._target_coord_file = target_coordinates_file
#        if "target_coordinates_file" in kwargs.keys():
#
#            self._target_coord_file = kwargs.pop("target_coordinates_file") 
        
    @staticmethod
    def fetch_frames(input, mode=None):
        # If input is an image, make a copy
        # Otherwise it is assumed to be a camera object
        # that returns frames upon iterating it.
        # Capture 5 frames and take the median intensity for each pixel
        # i.e. get an image that represents the median of 5 frames

        modes_min = {"target_detection": 90, "roi_builder": 20, "tracker": 0}
        modes_n = {"target_detection": 5, "roi_builder": 5}
        next_mode = {"target_detection": "roi_builder", "roi_builder": "tracker"}

        accum = []
        if isinstance(input, np.ndarray):
            accum = np.copy(input)

        else:
            for i, (_, frame) in enumerate(input):
                output_path = os.path.join(os.environ["HOME"], f"frame_{str(i).zfill(3)}_{mode}.png")
                cv2.imwrite(output_path, frame)
                logging.warning(f"I: {i}")
                logging.warning(f"mean_intensity: {np.mean(frame)}")
                if i  == modes_n[mode]-1:
                    break
                if mode is not None:
                    mean_intensity = np.mean(frame)
                    logging.warning(mean_intensity)
                    if mean_intensity < modes_min[mode]:
                        modes_n[next_mode[mode]] -= 1
                accum.append(frame)

            accum = np.median(np.array(accum),0).astype(np.uint8)

        output_path = os.path.join(os.environ["HOME"], f"{mode}.png")
        logging.info(f"Saving {mode} accum to {output_path}")
        cv2.imwrite(output_path, accum)
        
        return accum

    def build(self, input):
        """
        Uses an input (image or camera) to build ROIs.
        When a camera is used, several frames are acquired and averaged to build a reference image.

        :param input: Either a camera object, or an image.
        :type input: :class:`~ethoscope.hardware.input.camera.BaseCamera` or :class:`~numpy.ndarray`
        :return: list(:class:`~ethoscope.core.roi.ROI`)
        """

        accum = self.fetch_frames(input, mode="target_detection")     

        try:
            if self.__class__.__name__ == "FSLTargetROIBuilder":
                cv2.imwrite("/root/target_detection_build.png", accum)
                img, M, rois = self._rois_from_img(accum, camera=input)
            else:
                rois = self._rois_from_img(accum)

        except Exception as e:
            if not isinstance(input, np.ndarray):
                del input
            logging.error(traceback.format_exc())
            raise e

        rois_w_no_value = [r for r in rois if r.value is None]

        if len(rois_w_no_value) > 0:
            rois = self._spatial_sorting(rois)
        else:
            rois = self._value_sorting(rois)

        if self.__class__.__name__ == "FSLTargetROIBuilder":
            result = (img, M, rois)
        else:
            result = rois

        return result



    def _rois_from_img(self,img):
        raise NotImplementedError

    def _spatial_sorting(self, rois):
        '''
        returns a sorted list of ROIs objects it in ascending order based on the first value in the rectangle property
        '''
        return sorted(rois, key=lambda x: x.rectangle[0], reverse=False)

    def _value_sorting(self, rois):
        '''
        returns a sorted list of ROIs objects it in ascending order based on the .value property
        '''
        return sorted(rois, key=lambda x: x.value, reverse=False)


class DefaultROIBuilder(BaseROIBuilder):


    """
    The default ROI builder. It simply defines the entire image as a unique ROI.
    """
    _description = {"overview": "The default ROI builder. It simply defines the entire image as a unique ROI.", "arguments": []}


    def _rois_from_img(self,img):
        h, w = img.shape[0],img.shape[1]
        return[
            ROI(np.array([
                (   0,        0       ),
                (   0,        h -1    ),
                (   w - 1,    h - 1   ),
                (   w - 1,    0       )])
            , idx=1)]

