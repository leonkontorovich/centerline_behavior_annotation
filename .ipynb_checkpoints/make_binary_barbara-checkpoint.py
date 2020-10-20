#read and write tiff video for binary

#import pckgs
import cv2
import tifffile as tiff
import numpy as np
import matplotlib.pyplot as plt
import argparse

ap = argparse.ArgumentParser()
ap.add_argument("-i", "--input_filename", required=True, help="path to input file")

args = vars(ap.parse_args())

input_filename=args['input_filename']

output_filename='/groups/zimmer/shared_projects/Barbara_Ulises/Labeller_Test/multiple_skeleton/output_binary/'+args['input_filename'][-14:-5]+'_binary.tiff'

print('\n')
print('input:')
print(input_filename)
print('\n')
print('\n')
print('output:')
print(output_filename)



with tiff.TiffWriter(output_filename, bigtiff=True) as tif_writer:
    with tiff.TiffFile(input_filename, multifile=False) as tif:
        for i, page in enumerate(tif.pages):
            #loads the first frame and inverts it
            img=page.asarray()
            #img=cv2.bitwise_not(img)

            #median Blur
            img[:] = cv2.medianBlur(img,3)
            
            #apply threshold
            ret, new_img = cv2.threshold(img,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)          
            plt.imshow(new_img)
            #find contours
            _, contours, hierarchy = cv2.findContours(new_img, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
            #contours = contours[0] if len(contours) == 2 else contours[1]
            
            #list areas of contours, find MAX, draw contours from MAX area
            areas=[]
            for j in range(0, len(contours)):
                areas.append(cv2.contourArea(contours[j]))
            worm_contour=np.where(areas==np.asarray(areas).max())
            worm_contour=np.asarray(worm_contour)
            img_contours = np.zeros(img.shape)
            img[:]=cv2.drawContours(img_contours,contours, worm_contour, 255, -1)

            img_contours=np.array(img_contours, dtype=np.uint8)

            tif_writer.save(img)
            #if i ==150: break
            