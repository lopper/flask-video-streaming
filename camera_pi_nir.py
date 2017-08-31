import io
import time
import picamera
from base_camera import BaseCamera
import numpy as np
import cv2
import picamera.array
from PIL import Image
class Camera(BaseCamera):
    @staticmethod
    def disp_multiple(im1=None, im2=None, im3=None, im4=None):
        """
        Combines four images for display.
        """
        height, width = im1.shape

        combined = np.zeros((2 * height, 2 * width, 3), dtype=np.uint8)

        combined[0:height, 0:width, :] = cv2.cvtColor(im1, cv2.COLOR_GRAY2RGB)
        combined[height:, 0:width, :] = cv2.cvtColor(im2, cv2.COLOR_GRAY2RGB)
        combined[0:height, width:, :] = cv2.cvtColor(im3, cv2.COLOR_GRAY2RGB)
        combined[height:, width:, :] = cv2.cvtColor(im4, cv2.COLOR_GRAY2RGB)

        return combined

    @staticmethod
    def label(image, text):
        """
        Labels the given image with the given text
        """
        return cv2.putText(image, text, (0, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, 255)

    @staticmethod
    def contrast_stretch(im):
        """
        Performs a simple contrast stretch of the given image, from 5-95%.
        """
        in_min = np.percentile(im, 5)
        in_max = np.percentile(im, 95)

        out_min = 0.0
        out_max = 255.0

        out = im - in_min
        out *= ((out_min - out_max) / (in_min - in_max))
        out += in_min

        return out

    @staticmethod
    def get_ndvi(nir, c):
        bottom = (nir.astype(float) + c.astype(float))
        bottom[bottom == 0] = 0.01  # Make sure we don't divide by zero!

        ndvi = (nir.astype(float) - c.astype(float)) / bottom
        ndvi = Camera.contrast_stretch(ndvi)
        ndvi = ndvi.astype(np.uint8)
        return ndvi

    @staticmethod
    def frames():
        with picamera.PiCamera() as camera:
            # let camera warm up
            # Set the camera resolution
            x = 400
            camera.resolution = (int(1.33 * x), x)
            time.sleep(3)

            with picamera.array.PiRGBArray(camera) as stream:
                for foo in camera.capture_continuous(stream, format='rgb',
                                                     use_video_port=True):
                    # return current frame
                    stream.seek(0)
                    image = foo.array
                    # Get the individual colour components of the image
                    r = image[:,:,0]  
                    g = image[:,:,1]  
                    b = image[:,:,2] 

                    # Calculate the NDVI
                    gnvdi = Camera.get_ndvi(r, g)
                    bndvi = Camera.get_ndvi(r,b)
                    
                    # Do the labelling
                    Camera.label(r, 'NIR')
                    Camera.label(gnvdi, 'GNVDI')
                    Camera.label(b, 'BLUE')
                    Camera.label(bndvi, 'BNDVI')

                    # Combine ready for display
                    combined = Camera.disp_multiple(r, gnvdi, b, bndvi)
      		          
                    # apply color map
                    nv = cv2.applyColorMap(combined, cv2.COLORMAP_JET)
                
                    nImage = Image.fromarray(nv)
                    imgByteArr = io.BytesIO()
		    nImage.save(imgByteArr, format='JPEG')
		    imgByteArr = imgByteArr.getvalue()


                    yield imgByteArr
                    # reset stream for next frame
                    stream.seek(0)
                    stream.truncate()
