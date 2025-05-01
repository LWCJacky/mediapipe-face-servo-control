import cv2
import numpy as np
from mediapipe import solutions
from mediapipe.framework.formats import landmark_pb2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# 假设的相机内参
focal_length = 1000  # 焦距，单位为像素
center_x = 320  # 图像中心 X 坐标（假设 640x480 图像）
center_y = 240  # 图像中心 Y 坐标（假设 640x480 图像）


# 定义嘴巴位置计算函数
def get_mouth_position(landmarks):
    # 定义 Mediapipe 中嘴巴的关键点索引
    upper_lip_idx = 13
    lower_lip_idx = 14
    nose_tip_idx = 1

    # 提取相关的 3D 坐标
    upper_lip = np.array([landmarks[upper_lip_idx].x, landmarks[upper_lip_idx].y, landmarks[upper_lip_idx].z])
    lower_lip = np.array([landmarks[lower_lip_idx].x, landmarks[lower_lip_idx].y, landmarks[lower_lip_idx].z])
    nose_tip = np.array([landmarks[nose_tip_idx].x, landmarks[nose_tip_idx].y, landmarks[nose_tip_idx].z])

    # 计算嘴巴的中心位置
    mouth_center = (upper_lip + lower_lip) / 2
    # 计算相对鼻尖的位置
    mouth_position_world = mouth_center - nose_tip
    return mouth_position_world


# 定义绘制网格和坐标的函数
def draw_grid(image, step=50):
    h, w, _ = image.shape

    for y in range(0, h, step):
        cv2.line(image, (0, y), (w, y), (200, 200, 200), 1)

    for x in range(0, w, step):
        cv2.line(image, (x, 0), (x, h), (200, 200, 200), 1)

    center_x, center_y = w // 2, h // 2
    cv2.line(image, (center_x, 0), (center_x, h), (0, 255, 0), 2)
    cv2.line(image, (0, center_y), (w, center_y), (0, 255, 0), 2)

    return center_x, center_y


# 定义绘制面部特征点和嘴巴位置的函数
def draw_landmarks_on_image(rgb_image, detection_result):
    face_landmarks_list = detection_result.face_landmarks
    annotated_image = np.copy(rgb_image)

    for idx in range(len(face_landmarks_list)):
        face_landmarks = face_landmarks_list[idx]
        face_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
        face_landmarks_proto.landmark.extend([
            landmark_pb2.NormalizedLandmark(x=landmark.x, y=landmark.y, z=landmark.z) for landmark in face_landmarks
        ])

        # 计算嘴巴的位置
        mouth_position = get_mouth_position(face_landmarks)
        print(f"Mouth Position (Relative to Nose): {mouth_position}")

        # 将嘴巴位置转换为 2D 屏幕坐标
        z = 1  # 假设 Z = 1，实际情况中 Z 值会依据实际场景调整
        x = mouth_position[0] * focal_length / z + center_x
        y = -mouth_position[1] * focal_length / z + center_y

        # 绘制嘴巴位置
        cv2.circle(annotated_image, (int(x), int(y)), 5, (0, 0, 255), -1)
        cv2.putText(annotated_image, f"Mouth: ({int(x)}, {int(y)})",
                    (int(x) + 10, int(y) - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

    return annotated_image


# 初始化 Mediapipe 的 FaceLandmarker 物件
base_options = python.BaseOptions(model_asset_path='csic.dest')
options = vision.FaceLandmarkerOptions(base_options=base_options,
                                       output_face_blendshapes=True,
                                       output_facial_transformation_matrixes=True,
                                       num_faces=1)
detector = vision.FaceLandmarker.create_from_options(options)

# 开始读取摄像头
cap = cv2.VideoCapture(0)

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        print("无法获取视频帧，可能摄像头未连接")
        break

    # 将每一帧转换为 Mediapipe Image 格式
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

    # 执行人脸特征点检测
    detection_result = detector.detect(mp_image)

    # 绘制网格
    draw_grid(frame)

    # 绘制检测结果并计算嘴巴位置
    if detection_result.face_landmarks:
        annotated_image = draw_landmarks_on_image(rgb_frame, detection_result)
        annotated_image_bgr = cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR)
    else:
        annotated_image_bgr = frame

    # 显示画面
    cv2.imshow('Face Landmarks with Grid and Mouth Position', annotated_image_bgr)

    # 按 'q' 键退出
    if cv2.waitKey(5) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
