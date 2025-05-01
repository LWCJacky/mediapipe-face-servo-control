import cv2
import numpy as np
from mediapipe import solutions
from mediapipe.framework.formats import landmark_pb2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import math
from pid import PIDController
import serial
import configparser
import time
import logging
from DynamicTable import DynamicTable
import warnings
warnings.filterwarnings("ignore", module="google.protobuf")
 # 設置 logging 基本配置
logging.basicConfig(
    filename='app.log',            # 日誌輸出的文件名
    filemode='a',                  # 'a' 表示追加模式 (append)，'w' 表示覆蓋模式 (write)
    level=logging.DEBUG,           # 記錄的最低層級(DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(levelname)s - %(message)s',  # 日誌格式
    datefmt='%Y-%m-%d %H:%M:%S'    # 日期格式
)
# -------配置文件定義--------
# 創建 ConfigParser 對象
logging.info("加載配置文件中...")
config = configparser.ConfigParser()
# 讀取配置文件
config.read('config.ini')
port = config['settings']['port']  # 根據實際情況設置COM7
baudrate = config['settings']['baudrate']  # 根據設備設定的波特率
draw_grid=config['settings'].getboolean('draw_grid')
# -------------------------
#
logging.info("配置文件讀取成功")

# 定義用於計算角度的函數
def calculate_face_orientation(landmarks):
    # 使用 Mediapipe 的面部特徵點索引
    left_eye_idx = 33  # 左眼外角
    right_eye_idx = 263  # 右眼外角
    nose_tip_idx = 1  # 鼻尖
    chin_idx = 152  # 下巴

    # 提取相關的 3D 座標
    left_eye = np.array([landmarks[left_eye_idx].x, landmarks[left_eye_idx].y, landmarks[left_eye_idx].z])
    right_eye = np.array([landmarks[right_eye_idx].x, landmarks[right_eye_idx].y, landmarks[right_eye_idx].z])
    nose_tip = np.array([landmarks[nose_tip_idx].x, landmarks[nose_tip_idx].y, landmarks[nose_tip_idx].z])
    chin = np.array([landmarks[chin_idx].x, landmarks[chin_idx].y, landmarks[chin_idx].z])

    # 計算 Roll (左右傾斜)
    eye_diff = right_eye - left_eye
    roll_angle = math.atan2(eye_diff[1], eye_diff[0]) * (180.0 / math.pi)

    # 計算 Pitch (上下傾斜)
    face_height = chin - nose_tip
    pitch_angle = math.atan2(face_height[1], face_height[2]) * (180.0 / math.pi)

    # 計算 Yaw (左右旋轉)
    face_width = right_eye - nose_tip
    yaw_angle = math.atan2(face_width[0], face_width[2]) * (180.0 / math.pi)

    return pitch_angle, yaw_angle, roll_angle

# 定義繪製面部特徵點的函數
def draw_landmarks_on_image(rgb_image, detection_result):
    face_landmarks_list = detection_result.face_landmarks
    annotated_image = np.copy(rgb_image)

    for idx in range(len(face_landmarks_list)):

        face_landmarks = face_landmarks_list[idx]


        face_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
        face_landmarks_proto.landmark.extend([
            landmark_pb2.NormalizedLandmark(x=landmark.x, y=landmark.y, z=landmark.z) for landmark in face_landmarks
        ])

        if draw_grid:
            solutions.drawing_utils.draw_landmarks(
                image=annotated_image,
                landmark_list=face_landmarks_proto,
                connections=mp.solutions.face_mesh.FACEMESH_TESSELATION,
                landmark_drawing_spec=None,
                connection_drawing_spec=mp.solutions.drawing_styles.get_default_face_mesh_tesselation_style()
            )
            solutions.drawing_utils.draw_landmarks(
                image=annotated_image,
                landmark_list=face_landmarks_proto,
                connections=mp.solutions.face_mesh.FACEMESH_CONTOURS,
                landmark_drawing_spec=None,
                connection_drawing_spec=mp.solutions.drawing_styles.get_default_face_mesh_contours_style()
            )
            solutions.drawing_utils.draw_landmarks(
                image=annotated_image,
                landmark_list=face_landmarks_proto,
                connections=mp.solutions.face_mesh.FACEMESH_IRISES,
                landmark_drawing_spec=None,
                connection_drawing_spec=mp.solutions.drawing_styles.get_default_face_mesh_iris_connections_style()
            )

        # 計算人臉角度
        pitch, yaw, roll = calculate_face_orientation(face_landmarks)
        # print(f'Pitch: {pitch:.2f}, Yaw: {yaw:.2f}, Roll: {roll:.2f}')
        #計算鼻尖3d座標
        nose_tip_idx=1
        nose_tip = np.array([face_landmarks[nose_tip_idx].x, face_landmarks[nose_tip_idx].y, face_landmarks[nose_tip_idx].z])
        # print(nose_tip)
    return annotated_image,nose_tip
def send_to_serial(port, baudrate, message):
    """
    通過串口發送文字到控制器
    :param port: 串口號，例如 'COM3' 或 '/dev/ttyUSB0'
    :param baudrate: 波特率，例如 9600
    :param message: 要發送的文字
    """
    try:
        # 打開串口
        with serial.Serial(port, baudrate, timeout=1) as ser:
            # 等待一會兒以確保串口初始化完成
            # time.sleep(0.01)

            # 將文字轉換為字節數據並發送
            ser.write(message.encode())
            # print(f"已發送: {message}")

            # 接收控制器回應（如果需要）
            response = ser.readline().decode().strip()
            if response:
                # print(f"接收到的回應: {response}")
                ...
            else:
                # print("無回應")
                logging.error(f"控制器無回應")
    except serial.SerialException as e:
        print(f"串口通信失敗: {e}")
        logging.error(f"串口通信失敗: {e}")
        raise


try:
    # 初始化 Mediapipe 的 FaceLandmarker 物件
    logging.info("初始化AI模型...")
    base_options = python.BaseOptions(model_asset_path='csic.dest')
    options = vision.FaceLandmarkerOptions(base_options=base_options,
                                           output_face_blendshapes=True,
                                           output_facial_transformation_matrixes=True,
                                           num_faces=1)
    detector = vision.FaceLandmarker.create_from_options(options)
    logging.info("AI模型以成功加載")
    logging.info("初始化視訊鏡頭...")
    # 開始讀取攝像頭
    cap = cv2.VideoCapture(int(config['settings']['cam_id']))
    logging.info("視訊鏡頭以初始化成功")
    logging.info("初始化PID參數...")
    pidX = PIDController(
            Kp=float(config['PID_X']['Kp']),
            Ki=float(config['PID_X']['Ki']),
            Kd=float(config['PID_X']['Kd']),
            setpoint=float(config['PID_X']['setpoint']),
            output_limits=(
                float(config['PID_X']['output_limits_min']),
                float(config['PID_X']['output_limits_max'])
            ),
            rate_limit=float(config['PID_X']['rate_limit'])
        )

        # 读取 PID_Y 参数
    pidY = PIDController(
        Kp=float(config['PID_Y']['Kp']),
        Ki=float(config['PID_Y']['Ki']),
        Kd=float(config['PID_Y']['Kd']),
        setpoint=float(config['PID_Y']['setpoint']),
        output_limits=(
            float(config['PID_Y']['output_limits_min']),
            float(config['PID_Y']['output_limits_max'])
        ),
        rate_limit=float(config['PID_Y']['rate_limit'])
    )
    logging.info("PID控制系統以加載")
    # pidX = PIDController(Kp=0.004, Ki=0.006, Kd=0.005, setpoint=0, output_limits=(-3, 3), rate_limit=0.5)
    # pidY = PIDController(Kp=0.004, Ki=0.006, Kd=0.005, setpoint=0, output_limits=(-3, 3), rate_limit=0.5)
    time.sleep(1)
    table = DynamicTable()
except Exception as e:
    logging.error(f"setup error: {e}")
    raise SystemExit("Error:初始化失敗")

# 初始化计时器变量
target_lost_time = None
delay_threshold = 4  # 延迟秒数
while cap.isOpened():
    success, frame = cap.read()
    if not success:
        # print("無法獲取視頻幀，可能攝像頭未連接")
        logging.error(f"無法獲取影像資料，鏡頭可能未連接")
        break

    # 將每一幀轉換為 Mediapipe Image 格式
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

    # 執行人臉特徵點檢測
    detection_result = detector.detect(mp_image)

    # 繪製檢測結果並計算角度
    if detection_result.face_landmarks:
        annotated_image,nose_tip = draw_landmarks_on_image(rgb_frame, detection_result)
        annotated_image_bgr = cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR)
        h, w, _ = annotated_image_bgr.shape
        center_x = w // 2
        center_y = h // 2
        cv2.circle(annotated_image_bgr, (center_x, center_y), 5, (0, 0, 255), -1)  # 設定 -1
        # 在?像中?制鼻尖位置

        # ??一化的鼻尖坐?映射到?像坐?中
        mapped_x = int(nose_tip[0] * w)
        mapped_y = int(nose_tip[1] * h)
        cv2.circle(annotated_image_bgr, (mapped_x, mapped_y), 5, (0, 255, 0), -1)
        distance = np.sqrt((mapped_x - center_x) ** 2 + (mapped_y - center_y) ** 2)
        # print(f"Distance between red and green points: {distance:.2f} pixels")
        # ?算??相???的xy坐?
        relative_x = mapped_x - center_x
        relative_y = center_y - mapped_y  # 注意 y ?是反向的（向上?正）


        pidYout = pidY.compute(relative_y, 0.5, reverse=True)
        pidXout = pidX.compute(relative_x, 0.5, reverse=True)
        # print(f"Green point relative to red point: x = {relative_x}, y = {relative_y};x修正值:{pidXout},y修正值{pidYout}")
        table.render_table(relative_x, relative_y, pidXout, pidYout)
        messagex = f"G1 X{pidXout} Y{pidYout} F1000\n"
        try:
            send_to_serial(port, baudrate, messagex)
        except:
            break

        cv2.arrowedLine(annotated_image_bgr, (mapped_x, mapped_y), (center_x, center_y), (255, 0, 0), 2, tipLength=0.2)
        # 分割四?象限
        cv2.line(annotated_image_bgr, (center_x, 0), (center_x, h), (255, 255, 255), 1)  # ??
        cv2.line(annotated_image_bgr, (0, center_y), (w, center_y), (255, 255, 255), 1)  # ??
        target_lost_time = None
    else:
        annotated_image_bgr = frame
        if target_lost_time is None:
            target_lost_time = time.time()  # 记录第一次丢失的时间
        elif time.time() - target_lost_time >= delay_threshold:
            # 如果丢失时间超过4秒，执行回到原点操作
            pidY.reset()
            pidX.reset()
            try:
                messagex2 = f"G1 X0 Y0 F1000\n"
                send_to_serial(port, baudrate, messagex2)
                table.render_table(0, 0, 0, 0)
            except:
                break
    cv2.imshow('Face Landmarks', annotated_image_bgr)

    # 按 'q' 鍵退出
    if cv2.waitKey(5) & 0xFF == ord('q'):
        try:
            messagex2 = f"G1 X0 Y0 F1000\n"
            send_to_serial(port, baudrate, messagex2)
            table.render_table(0, 0, 0, 0)
        except:
            break
        logging.info("程式正常退出")
        break

cap.release()
cv2.destroyAllWindows()
