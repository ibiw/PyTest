import os
import cv2
import numpy as np
import cvlib as cv

"""
    https://www.superdatascience.com/opencv-face-detection/
    pip install opencv-contrib-python
    https://www.superdatascience.com/opencv-face-recognition/
    https://www.datacamp.com/community/tutorials/face-detection-python-opencv
    img = cv2.cvtColor(img_raw, cv2.COLOR_BGR2RGB)
    https://www.cvlib.net/
    https://keras.io/
    https://github.com/arunponnusamy/object-detection-opencv
    
"""


def get_files(path, sub_dir=False):
    """get all files of the current folder"""
    for dirs, sub_dirs, _files in os.walk(path, topdown=True):
        if sub_dir:
            for _file in _files:
                yield dirs + '/' + _file
        else:
            for _file in _files:
                yield dirs + '/' + _file
            return


# load test iamge
test1 = cv2.imread('/home/rw/Pictures/unknow/andy.jpeg')
test2 = cv2.imread('/home/rw/Pictures/unknow/liu9.jpeg')
test_false = cv2.imread('/home/rw/Pictures/unknow/False-Positive-1.png')

# load cascade classifier training file for haarcascade
haar_face_cascade = cv2.CascadeClassifier(
    '/home/rw/anaconda3/lib/python3.6/site-packages/cv2/data/haarcascade_frontalface_alt.xml')

lbp_face_cascade = cv2.CascadeClassifier(
    '/home/rw/anaconda3/lib/python3.6/site-packages/cv2/data/lbpcascade_frontalface.xml')

#there is no label 0 in our training data so subject name for index/label 0 is empty
subjects = ["", "Liu", "Jacky"]


def face_detect_cvlib(files):

    for file in files:

        raw_img = cv2.imread(file)
        locations, confidences = cv.detect_face(raw_img)
        for location in locations:
            print(raw_img.shape)
            x1, y1, x2, y2 = location
            print(x1, y1, x2, y2)
            new_img = raw_img[y1:y2, x1:x2]
            draw_rectangle(raw_img, location)
            print(location)


        # cv2.imshow('Face', new_img)
        # cv2.waitKey(1000)
    # cv2.destroyAllWindows()


def detect_faces(f_cascade, colored_img, scale_factor=1.2):
    # just making a copy of image passed, so that passed image is not changed
    img_copy = colored_img.copy()

    # convert the test image to gray image as opencv face detector expects gray images
    gray = cv2.cvtColor(img_copy, cv2.COLOR_BGR2GRAY)

    # let's detect multiscale (some images may be closer to camera than others) images
    faces = f_cascade.detectMultiScale(gray, scaleFactor=scale_factor, minNeighbors=5)

    # go over list of faces and draw them as rectangles on original colored img
    for (x, y, w, h) in faces:
        cv2.rectangle(img_copy, (x, y), (x + w, y + h), (0, 255, 0), 2)

    return img_copy


# function to detect face using OpenCV
def detect_face(img):
    # convert the test image to gray scale as opencv face detector expects gray images
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # load OpenCV face detector, I am using LBP which is fast
    # there is also a more accurate but slow: Haar classifier
    face_cascade = cv2.CascadeClassifier(
        '/home/rw/anaconda3/lib/python3.6/site-packages/cv2/data/lbpcascade_frontalface.xml')

    # let's detect multiscale images(some images may be closer to camera than others)
    # result is a list of faces
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5)

    # if no faces are detected then return original img
    if (len(faces) == 0):
        return None, None

    # under the assumption that there will be only one face,
    # extract the face area
    x, y, w, h = faces[0]

    print(faces[0])
    # return only the face part of the image
    return gray[y:y + w, x:x + h], faces[0]


def face_get_cvlib(files):
    """return gray face img and its locations"""
    _files = [files] if type(files) is not list else files

    for file in _files:
        __faces = []

        raw_img = cv2.imread(file) if type(file) is str else file
        try:
            face_locations, confidences = cv.detect_face(raw_img)
            for face_location in face_locations:
                print(face_location)
                # print(raw_img.shape)
                x1, y1, x2, y2 = face_location
                # print(x1, y1, x2, y2)
                # new_img = raw_img[y1:y2, x1:x2]
                new_img = cv2.cvtColor(raw_img[y1:y2, x1:x2], cv2.COLOR_BGR2GRAY)
                __faces.append(new_img)
        except cv2.error:
            print('{} -- face not detected'.format(file))

    #         print(type(new_img))
    #         draw_rectangle(raw_img, face_location)
    #         print(face_location)
    #
    #     cv2.imshow('Face', raw_img)
    #     cv2.waitKey(1000)
    # cv2.destroyAllWindows()
        if __faces:
            return __faces, face_locations
        else:
            return None, None


# this function will read all persons' training images, detect face from each image
# and will return two lists of exactly same size, one list
# of faces and another list of labels for each face
def prepare_training_data(data_folder_path):

    # ------STEP-1--------
    # get the directories (one directory for each subject) in data folder
    dirs = os.listdir(data_folder_path)

    # list to hold all subject faces
    faces = []
    # list to hold labels for all subjects
    labels = []

    # let's go through each directory and read images within it
    for dir_name in dirs:

        # our subject directories start with letter 's' so
        # ignore any non-relevant directories if any
        if not dir_name.startswith("s"):
            continue

        # ------STEP-2--------
        # extract label number of subject from dir_name
        # format of dir name = slabel
        # , so removing letter 's' from dir_name will give us label
        label = int(dir_name.replace("s", ""))

        # build path of directory containing images for current subject subject
        # sample subject_dir_path = "training-data/s1"
        subject_dir_path = data_folder_path + "/" + dir_name

        # get the images names that are inside the given subject directory
        subject_images_names = os.listdir(subject_dir_path)

        # ------STEP-3--------
        # go through each image name, read image,
        # detect face and add face to list of faces
        for image_name in subject_images_names:

            # ignore system files like .DS_Store
            if image_name.startswith("."):
                continue

            # build image path
            # sample image path = training-data/s1/1.pgm
            image_path = subject_dir_path + "/" + image_name
            print(image_path)

            # read image
            # image = cv2.imread(image_path)

            # display an image window to show the image


            # detect face
            # face, rect = detect_face(image)
            face, rect = face_get_cvlib(image_path)


            # ------STEP-4--------
            # for the purpose of this tutorial
            # we will ignore faces that are not detected
            if face is not None:
                # training date only has one face
                face = face[0]
                # add face to list of faces
                faces.append(face)
                # add label for this face
                labels.append(label)
                print(label)
            else:
                print('None')
                cv2.imshow("Training on image...", image)
                cv2.waitKey(1000)

    cv2.destroyAllWindows()
    cv2.waitKey(1)
    cv2.destroyAllWindows()

    return faces, labels


# let's first prepare our training data
# data will be in two lists of same size
# one list will contain all the faces
# and the other list will contain respective labels for each face
print("Preparing data...")
faces, labels = prepare_training_data("/home/rw/Pictures/test")
print("Data prepared")

# print total faces and labels
print("Total faces: ", len(faces))
print("Total labels: ", len(labels))

# create our LBPH face recognizer
# face_recognizer = cv2.face.createLBPHFaceRecognizer()
face_recognizer = cv2.face.LBPHFaceRecognizer_create()


# train our face recognizer of our training faces
face_recognizer.train(faces, np.array(labels))


# function to draw rectangle on image
# according to given (x, y) coordinates and
# given width and heigh
def draw_rectangle(img, rect):
    (x, y, w, h) = rect
    # cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
    cv2.rectangle(img, (x, y), (w, h), (0, 255, 0), 2)

###
# function to draw text on give image starting from
# passed (x, y) coordinates.
def draw_text(img, text, x, y):
    cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_PLAIN, 1.5, (0, 255, 0), 2)


# this function recognizes the person in image passed
# and draws a rectangle around detected face with name of the
# subject
# def predict(test_img):
#     # make a copy of the image as we don't want to change original image
#     img = test_img.copy()
#     # detect face from the image
#     # face, rect = detect_face(img)
#     face, rect = face_get_cvlib(img)
#     face = face[0]
#     rect = rect[0]
#
#
#     # predict the image using our face recognizer
#     label = face_recognizer.predict(face)
#     print(label)
#     # get name of respective label returned by face recognizer
#     label_text = subjects[label[0]]
#
#     # draw a rectangle around face detected
#     draw_rectangle(img, rect)
#     # draw name of predicted person
#     draw_text(img, label_text, rect[0], rect[1] - 5)
#
#     return img

def predict(test_img):
    # make a copy of the image as we don't want to change original image
    img = test_img.copy()
    # detect face from the image
    # face, rect = detect_face(img)
    _faces, _rects = face_get_cvlib(img)
    # print(_faces, _rects)
    # if len(_rects) == 1:
    #     _faces = [_faces]
    #     _rects = [_rects]

    for i, face, in enumerate(_faces):

        rect = _rects[i]
        # predict the image using our face recognizer
        label = face_recognizer.predict(face)
        print(label)
        # get name of respective label returned by face recognizer
        label_text = subjects[label[0]]

        # draw a rectangle around face detected
        draw_rectangle(img, rect)
        # draw name of predicted person
        draw_text(img, label_text, rect[0], rect[1] - 5)

    return img

print("Predicting images...")

# load test images
# test_img1 = cv2.imread("test-data/test1.jpg")
# test_img2 = cv2.imread("test-data/test2.jpg")

test_img1 = cv2.imread('/home/rw/Pictures/test/test/p2.jpeg')
test_img2 = cv2.imread('/home/rw/Pictures/test/test/p2.jpeg')

# perform a prediction
predicted_img1 = predict(test_img1)
predicted_img2 = predict(test_img2)
print("Prediction complete")

# display both images
cv2.imshow(subjects[1], predicted_img1)
cv2.imshow(subjects[2], predicted_img2)
cv2.waitKey(0)
cv2.destroyAllWindows()



# or use EigenFaceRecognizer by replacing above line with
# face_recognizer = cv2.face.createEigenFaceRecognizer()

# or use FisherFaceRecognizer by replacing above line with
# face_recognizer = cv2.face.createFisherFaceRecognizer()


# face_dected_image = detect_faces(lbp_face_cascade, test_false, scale_factor=1.1)
# cv2.imshow('Test Image', face_dected_image)
# cv2.waitKey(0)
# cv2.destroyAllWindows()

# path = '/home/rw/Pictures'
#
# files = get_files(path, sub_dir=True)
#
# for file in files:
#     print(file)



