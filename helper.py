import numpy as np
import cv2
import serial
import time
import pygame
import sys 
from pygame.locals import *
import math as math

def frame_timer(frame):
    
    if frame < 4000:
        return frame
    else:
        return frame-4000

def car_info_backup(frame_counter, center, center_pre, car_cnt, car_cnt_pre, mark1_center, mark1_center_pre, mark2_center, mark2_center_pre, angle, angle_pre):
    
    if frame_counter != 0:
        return center, car_cnt, mark1_center, mark2_center, angle
    else:
        return center_pre, car_cnt, mark1_center_pre, mark2_center_pre, angle_pre


def board_pos_deter(contours):

    board_index = 0
    while(cv2.contourArea(contours[board_index]) < 50000): # find white board contour
        board_index = board_index + 1

    board_cnt = contours[board_index]
    rect = cv2.minAreaRect(board_cnt)
    (x,y),(w,h), angle = rect

    return (x, y), (w, h), angle, board_cnt

def car_pos_deter(contours):

    car_center = (0, 0)
    mark1_center = (0, 0)
    mark2_center = (0, 0)
    rectMax_index = 0
    rectMax_area = 0

    for i in range(0, len(contours)):
        cnt = contours[i]
        cntarea = cv2.contourArea(cnt, 0)

        # car outer contour 500~820
        if cntarea > 500 and cntarea < 820: 
            rect = cv2.minAreaRect(cnt)
            (car_x, car_y), (car_w, car_h), angle = rect
            rect_area = car_w*car_h
            extent = float(cntarea)/rect_area

            if extent >= 0.9:
                if cntarea > rectMax_area:
                    rectMax_area = cntarea
                    rectMax_index = i
                    car_center = (car_x, car_y)


    car_cnt = contours[rectMax_index]

    mark1_is_get = 0
    mark2_is_get = 0
    index = 0

    while index < len(contours):
    	cnt = contours[index]
        cntarea = cv2.contourArea(cnt, 0)
        # car mark1 contour 50~100
        if cntarea > 50 and cntarea < 80:
                rect = cv2.minAreaRect(cnt)
                # print(cntarea)
                (mark1_x, mark1_y), (mark1_w, mark1_h), mark1_angle = rect
                rect_area = mark1_w*mark1_h
                extent = float(cntarea)/rect_area

                if extent >= 0.7 and cv2.pointPolygonTest(car_cnt, (mark1_x, mark1_y), False) == 1:
                    #print('extent1 is:', extent)
                    mark1_center = (mark1_x, mark1_y)
                    mark1_is_get = 1


        # car mark1 contour 20~50
        elif  cntarea > 30 and cntarea < 50:
                rect = cv2.minAreaRect(cnt)
                # print(cntarea)
                (mark2_x, mark2_y), (mark2_w, mark2_h), mark2_angle = rect
                rect_area = mark2_w*mark2_h
                extent = float(cntarea)/rect_area

                if extent >= 0.7 and cv2.pointPolygonTest(car_cnt, (mark2_x, mark2_y), False) == 1:
                    #print('extent2 is:', extent)
                    mark2_center = (mark2_x, mark2_y)
                    mark2_is_get = 1
        
        if (mark1_is_get == 1) and (mark2_is_get == 1):
        	break
        else:
        	index = index+1

    return car_center, car_cnt, mark1_center, mark2_center

def axis_convert2_normal(point_xy_in_video):

    return (point_xy_in_video[0], -point_xy_in_video[1])

def vector_direction(start_pt, end_pt):

    start_pt = axis_convert2_normal(start_pt)
    end_pt = axis_convert2_normal(end_pt)
    pi = 3.1415926
    angle_in_rad = math.atan2((end_pt[1] - start_pt[1]), (end_pt[0] - start_pt[0]))
    angle_in_degree = (angle_in_rad/pi)*180
    return angle_in_degree

def car_angle_deter(car_center, mark1_center, mark2_center):

    default_direction = 90 #unit:degree
    angle1_in_degree = vector_direction(car_center, mark1_center)
    angle2_in_degree = vector_direction(car_center, mark2_center)
    print (angle1_in_degree)
    print (angle2_in_degree)


    if angle1_in_degree <=0 and angle2_in_degree >=0:
        angle_diff = abs(angle2_in_degree - angle1_in_degree)
        if angle_diff >= 200 and angle_diff <= 290:
            candidate1 = angle1_in_degree - 45
            candidate2 = angle2_in_degree + 45
            if candidate1 <= 0 and candidate1 >= -180:
                turnAngle = candidate1 - default_direction    #unit:degree
            else:
                turnAngle = candidate2 - default_direction
        else:
        	turnAngle = angle1_in_degree - 45 - default_direction

    else:
        angle_diff = abs(angle2_in_degree - angle1_in_degree)
        if angle_diff >= 70 and angle_diff <= 110:
            turnAngle = angle1_in_degree - angle_diff/2 - default_direction    #unit:degree

        else:
            turnAngle = angle1_in_degree - 45 - default_direction

    print("turn!!!", turnAngle)
    return turnAngle

def car_pos_is_table(car_center, car_center_pre, mark1_center, mark1_center_pre, mark2_center, mark2_center_pre, pixel_diff, angle, angle_pre, degree_diff):
    car_center_diff = math.sqrt((car_center[1] - car_center_pre[1]) * (car_center[1] - car_center_pre[1]) + (car_center[0] - car_center_pre[0]) * (car_center[0] - car_center_pre[0]))
    mark1_diff = math.sqrt((mark1_center[1] - mark1_center_pre[1]) * (mark1_center[1] - mark1_center_pre[1]) + (mark1_center[0] - mark1_center_pre[0]) * (mark1_center[0] - mark1_center_pre[0]))
    mark2_diff = math.sqrt((mark2_center[1] - mark2_center_pre[1]) * (mark2_center[1] - mark2_center_pre[1]) + (mark2_center[0] - mark2_center_pre[0]) * (mark2_center[0] - mark2_center_pre[0]))
    angle_diff = abs(angle - angle_pre)

    if car_center_diff > pixel_diff:
        car_center_stable = 0
    else:
        car_center_stable = 1


    if mark1_diff > pixel_diff:
        mark1_stable = 0
    else:
        mark1_stable = 1


    if mark2_diff > pixel_diff:
        mark2_stable = 0
    else:
        mark2_stable = 1


    if angle_diff > degree_diff:
    	angle_stable = 0
    else:
    	angle_stable = 1

	return (car_center_stable and mark1_stable and mark2_stable and angle_stable)

def command_calculator(target_direction, current_direction, angle_param):

        command = 'q'
        
        if (target_direction - current_direction <= angle_param and target_direction - current_direction >=0) or (target_direction - current_direction >= (-angle_param) and target_direction - current_direction <= 0):
            command = 'w' ## forward

        elif (target_direction - current_direction > angle_param and target_direction - current_direction <=  180 - angle_param):
            command = 'a' 

        elif target_direction - current_direction < (-angle_param) and target_direction - current_direction >=  -(180 - angle_param):
            command = 'd'

        else:
            command = 'a' ## backward

        return command