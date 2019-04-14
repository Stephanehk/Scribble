import cv2
import numpy as np
import json
import operator
import warnings
from PIL.Image import core as Image
from PIL import ImageDraw
from scipy.spatial import distance
from skimage.measure import structural_similarity as ssim

from app import run_ocr

warnings.filterwarnings("ignore")

class Letter ():
    def __init__ (self, image = None, letter = None, size = None, curvedness = None, time = None,x = None, y = None, SSD = None, area_dif = None, weighting = None):
        self.image = image
        self.letter = letter
        self.size = size
        self.curvedness = curvedness
        self.time = time
        self.x = x
        self.y = y
        self.SSD = SSD
        self.area_dif = area_dif
        self.weighting = weighting

def decode_roi (encoded, encoded_values):
    decoded = []
    for i in range(len(encoded)):
        decode = encoded.get(encoded_values[i])
        decoded.append(decode)
    return decoded

def encode_roi (text_rois):
    encoded = {}
    for i in range(len(text_rois)):
        encoded[i] = text_rois[i]
    encoded_values = list(encoded.keys())
    return encoded, encoded_values

def preserve_hiarchy (rois, startXs, startYs):
    #rois = [x for _,x in sorted(zip(startYs,rois))]
    hiarchal_roi = []
    lines = {}
    for i in range (len(rois)):
        line_x = {}
        roi = rois[i]
        startY = startYs[i]
        startX = startXs[i]
        for j in range (len(rois)):
            roi2 = rois[j]
            startY2 = startYs[j]
            startX2 = startXs[j]

            #if you are at the same values
            if startY == startY2 and startX == startX2:
                continue

            distance_y = np.abs(startY - startY2)
            #if the same y value
            if distance_y < 4:
                if roi not in line_x:
                    line_x[startX] = (roi)
                if roi2 not in line_x:
                    line_x[startX2] = (roi2)
        #if there are no two words on the same line
        if not line_x:
            line_x[0] = (roi)
        #sort x values (to get word order)
        line_x = sorted (line_x.items())
        #add only the rois to array
        word_line = []
        for l in line_x:
            word_line.append(l[1])
        lines[startY] = (word_line)
    #sort by line order
    lines = sorted (lines.items())
    #get every line
    for line in lines:
        #get every word in line
        for word in line[1]:
            #remove duplicates
            if word not in hiarchal_roi:
                #add to array
                hiarchal_roi.append(word)
    return hiarchal_roi

def get_countour_l(img, min_area):
    img_h,img_w,_ = img.shape
    imgray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    #thresh = cv2.adaptiveThreshold(imgray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2)
    _, thresh = cv2.threshold(imgray, 0, 255, cv2.THRESH_OTSU)
    thresh = 255 - thresh
    output = thresh.copy()
    img_with_rects = img.copy()
    #imgray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    #ret, thresh = cv2.threshold(output, 127, 255, 0)
    contours_, hierarchy = cv2.findContours(output, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    characters = []
    xs = []
    ys = []

    contours_ = sorted(contours_, key=lambda x: cv2.contourArea(x), reverse = True)
    contours_.pop(0)

    for i in range(len(contours_)):
        contour = contours_[i]
        area = cv2.contourArea(contour)
        x,y,w,h = cv2.boundingRect(contour)
        #print (str(w) + "X" + str(h))        #-------------------------------------------------------------
        if area>min_area:
            offset = 0
            if x+w+2 >= img_w and y+h+2 > img_h and x-2 >0 and y-2>0:
                offset = 2
            img_with_rects = cv2.rectangle(img_with_rects,(x-offset,y-offset),(x+w+offset,y+h+offset),(0,255,0),1)
            letter = img[y-offset: y+h+offset, x-offset: x+w+offset]
            characters.append(letter)
            xs.append(x-2)
            ys.append(y-2)
    return img_with_rects, characters, xs,ys

def create_object(image, bounds, letters, time):
    letter_objects = []
    image1 = image.copy()
    image = cv2.Canny(image, 100, 200)
    image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    for bound,letter in zip(bounds, letters):
        x1, y1 = bound.vertices[0].x, bound.vertices[0].y,
        x2,y2 = bound.vertices[1].x, bound.vertices[1].y
        x3,y3 = bound.vertices[2].x, bound.vertices[2].y
        x4,y4 = bound.vertices[3].x, bound.vertices[3].y,
        cv2.rectangle(image,(x4,y4),(x2,y2),(255,206,98),2)
        width = x3 - x4
        height = y3- y2
        offset = 3
        letter_img = image1[y4-offset:y4+height+offset,x4-offset:x4+width+offset]
        letter_object = Letter()
        letter_object.image = letter_img
        h,w = letter_img.shape
        letter_object.size = h*w
        letter_object.letter = letter
        letter_object.time = time
        letter_object.x = x4
        letter_object.y = y4
        letter_objects.append(letter_object)
    image = cv2.resize(image, (350, 350))
    return letter_objects, image

def distance_between_letters (letter_objects_b):
    distances = []
    for i in range(len(letter_objects_b)):
        x = letter_objects_b[i].x
        y = letter_objects_b[i].y
        try:
            n_x = letter_objects_b[i+1].x
            n_y = letter_objects_b[i+1].y
        except Exception as e:
            continue
        dst = distance.euclidean((x,y), (n_x,n_y))
        distances.append(dst)
    avg = np.mean(distances)
    return avg

def anal_word_shape (letter_objects):
    for letter in letter_objects:
        letter_image = letter.image
        h,w = letter_image.shape
        letter.size = h*w
        cannied = cv2.Canny(letter_image,100,200)


        #contours, hierarchy = cv2.findContours(cannied, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        # cv2.drawContours(letter.image,contours,-1,(0,255,0),1)
        # cv2.imshow("contours", letter.image)
        # cv2.waitKey(0)

def PolygonArea(corners):
    n = len(corners)  # of corners
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += corners[i][0] * corners[j][1]
        area -= corners[j][0] * corners[i][1]
    area = abs(area) / 2.0
    return area

def find_same_letters (letter_objects_b, letter_objects_a):
    same_letters = []
    visited = ""
    for object_b in letter_objects_b:
        current_letter_occurences = []
        letter_b = object_b.letter
        if letter_b in visited:
            continue
        visited+=letter_b
        current_letter_occurences.append(object_b)
        for object_a in letter_objects_a:
            letter_a = object_a.letter
            if letter_b == letter_a:
                current_letter_occurences.append(object_a)
        same_letters.append(current_letter_occurences)
    return same_letters

def anal_comparison (same_letters):
    structural_differences = []
    area_differences = []
    for same_letter in same_letters:
        total_s = []
        a_t_area = 0
        b_t_area = 0
        bs = []
        ass = []
        #seperate a's from b's
        for letter in same_letter:
            letter_with_anal = Letter()
            if letter.time == "b":
                bs.append(letter)
                b_t_area += letter.size
            else:
                ass.append(letter)
                a_t_area += letter.size
        if len(bs) and len(ass) != 0:
            if len(ass) > len(bs):
                longest = ass
            else:
                longest = bs

            for i in range (len(longest)):
                try:
                    b = bs[i]
                except Exception:
                    print(i)
                    b = bs[0]
                try:
                    a = ass[i]
                except Exception:
                    a = ass[0]

                h,w = b.image.shape
                a.image = cv2.resize(a.image, (w,h))
                s = ssim(b.image, a.image)
                total_s.append(s)
                avg_a_a = a_t_area/len(ass)
                avg_a_b = b_t_area/len(bs)
                diff_area = np.abs(avg_a_a - avg_a_b)
                avg_s = np.mean(total_s)

            structural_differences.append(avg_s)
            area_differences.append(diff_area)
        else:
            structural_differences.append(None)
            area_differences.append(None)
    return structural_differences, area_differences

def avg_line_shift(objects,x):
    arr = []
    for object in objects:
        arr.append(object.y)
    arr.sort()
    sub = [x-y for x, y in zip(arr, arr[1:])]
    value = np.average(sub)
    if value >= x:
        print("u done did it")
        return value
    else:
        return value

def heuristic (letter_anals,line_shift_difference, area_differences, change_in_dist):
    sum_letter_weights = 0
    area_differences = list(filter(lambda a: a != None, area_differences))
    avg_area_dif = np.mean(area_differences)
    for letter in letter_anals:
        sum_letter_weights += letter.weighting

    print ("sum of letter weightings: " + str(sum_letter_weights))
    print ("line_shift_difference: " + str(line_shift_difference))
    print ("avg_area_dif: " + str(avg_area_dif))
    print ("change_in_dist: " + str(change_in_dist))

    score = sum_letter_weights + 1/(line_shift_difference) + (1000/avg_area_dif) - (0.02*change_in_dist)
    #(0.5*sum_letter_weights) + (0.3*- line_shift_difference) + (0.2*avg_area_dif)
    return score

def creat_anal_objects (structural_differences, area_differences, same_letters):
    letter_anals = []
    letter_weightings = {"a":1,"b":1,"d":1,"e":1,"g":1,"p":1,"q":1,"s":1,"c":0.5,"f":0.5,"h":0.7,"i":0.4,"j":0.5,"k":0.5,"l":0.3,"m":0.5,
    "n":0.5,"o":0.5,"r":0.5,"t":0.7,"u":0.5,"v":0.5,"w":0.5,"x":0.5,"y":0.5,"z":0.5,"A":0.5,"B":0.7,"C":0.5,"D":1,"E":0.5,"F":0.5,"G":1,
    "H":0.5,"I":0.5,"J":0.5,"K":0.5, "L": 0.5, "M":0.5,"N":0.5,"O":0.5,"P":1,"Q":1, "R":1, "S": 0.5, "T":0.5,"U":0.5, "V": 0.5, "W": 0.5,
    "X": 0.5,"Y": 0.5, "Z": 0.5, "1": 0.5, "2": 1, "3":1, "4":0.5, "5":1, "6":1, "7":0.5,"8":1,"9":1,"0":0.5,None: 0}
    for i in range (len(structural_differences)):
        letter = same_letters[i][0].letter
        letter_anal = Letter()
        letter_anal.letter = letter
        letter_anal.SSD = structural_differences[i]
        letter_anal.area_dif = area_differences[i]
        try:
            letter_anal.weighting = letter_weightings.get(letter) * structural_differences[i]
        except Exception as e:
            letter_anal.weighting = 0
        letter_anals.append(letter_anal)
    return letter_anals

def fancy_image (image_with_rects_b, image_with_rects_a):
    cv2.imshow("img_b", image_with_rects_b)
    cv2.imshow("img_a", image_with_rects_a)
    cv2.waitKey(0)

def main(before, after):
    img_b = cv2.imread(before,0)
    bounding_boxes_b, letters_b = run_ocr.detect_document(before)
    letter_objects_b, image_with_rects_b= create_object(img_b, bounding_boxes_b, letters_b, "b")

    #anal_b = anal_word_shape(letter_objects_b)

    img_a = cv2.imread(after,0)
    bounding_boxes_a, letters_a = run_ocr.detect_document(after)
    letter_objects_a, image_with_rects_a = create_object(img_a, bounding_boxes_a, letters_a, "a")

    same_letters = find_same_letters (letter_objects_b, letter_objects_a)

    ls_b = avg_line_shift(letter_objects_b,10)
    ls_a = avg_line_shift(letter_objects_a,10)

    structural_differences, area_differences = anal_comparison (same_letters)
    line_shift_difference = np.abs(np.abs(ls_b) - np.abs(ls_a))
    dist_b = distance_between_letters(letter_objects_b)
    dist_a = distance_between_letters(letter_objects_a)
    change_in_dist = np.abs(dist_b - dist_a)

    letter_anals = creat_anal_objects(structural_differences, area_differences, same_letters)
    score = heuristic (letter_anals,line_shift_difference, area_differences, change_in_dist)
    #fancy_image (image_with_rects_b, image_with_rects_a)


    # print ("Avg structural differences")
    # print (structural_differences)
    # print ("Avg area differences")
    # print (area_differences)
    # print ("Avg line shift differences")
    # print (line_shift_difference)

    print ("score: " + str(score))
    if score < 10:
        message =  ("There are signs of dimensia in the handwriting")
    else:
        message = ("There are no signs of dimensia in the handwriting")
    return score, message, image_with_rects_b, image_with_rects_a

#main("/Users/2020shatgiskessell/Desktop/HandAnal/4_b.jpg", "/Users/2020shatgiskessell/Desktop/HandAnal/4_a.jpg")

#cv2.destroyAllWindows()
