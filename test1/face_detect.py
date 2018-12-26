import cv2
import cvlib as cv
from cvlib.object_detection import draw_bbox
import os
import face_recognition


def face_detection(files):
    if type(files) is str:
        files = [files]

    for file in files:
        img = cv2.imread(file)
        image = face_recognition.load_image_file(file)
        face_locations = face_recognition.face_locations(image, model='cnn')
        for face_location in face_locations:
            print(face_location)
            draw_rectangle(img, face_location)
            cv2.imshow('Face_Detection', img)
            cv2.waitKey(2000)
    cv2.destroyAllWindows()


def draw_rectangle(img, rect):
    (x, y, w, h) = rect
    cv2.rectangle(img, (x, y), (w, h), (0, 255, 0), 2)


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


# def face_detect_cvlib(files):
#     for file in files:
#
#         raw_img = cv2.imread(file)
#         faces, confidences = cv.detect_face(raw_img)
#         for face in faces:
#             print(raw_img.shape)
#             x1, y1, x2, y2 = face
#             print(x1, y1, x2, y2)
#             new_img = raw_img[y1:y2, x1:x2]
#             draw_rectangle(raw_img, face)
#             print(face)
#
#
#         cv2.imshow('Face', new_img)
#         cv2.waitKey(1000)
#     cv2.destroyAllWindows()


def face_detect_cvlib(files):
    for file in files:

        raw_img = cv2.imread(file)
        faces, confidences = cv.detect_face(raw_img)
        for face in faces:
            draw_rectangle(raw_img, face)

        cv2.imshow('Face', raw_img)
        cv2.waitKey(1000)

def obj_detect(files):
    if type(files) is str:
        files = [files]

    for file in files:
        raw_img = cv2.imread(file)
        bbox, label, conf = cv.detect_common_objects(raw_img)
        print(bbox, label, conf)
        output_image = draw_bbox(raw_img, bbox, label, conf)

        cv2.imshow('Obj', output_image)
        cv2.waitKey(1000)
        cv2.destroyAllWindows()


path = '/home/rw/Pictures/test/test'

files = get_files(path, sub_dir=True)
# face_detection(files)
face_detect_cvlib(files)
