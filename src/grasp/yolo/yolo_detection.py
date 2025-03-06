# -*- coding: utf-8 -*-
import warnings
warnings.filterwarnings('ignore')
from ultralytics import YOLO
import cv2
import numpy as np

class YOLODetection:
    def __init__(self, model_path):
        """
        初始化 YOLO 模型
        :param model_path: YOLO 模型的路径
        """
        self.model = YOLO(model=r'/home/zcy/project/ultralytics/runs/train/exp2/weights/best.pt')
        self.class_map = {
            "redball": 0,
            "yellowball": 1,
            "whiteball": 2,
            "pinkball": 3,
            "target": 4
        }


    def get_nao_camera_frame(self, video_service, video_client):
        """
        从 NAO 摄像头获取一帧图像并转换为 OpenCV 格式
        :param video_service: 传入的 NAO 视频服务
        :param video_client: 订阅的摄像头客户端
        :return: OpenCV 格式的图像
        """
        nao_image = video_service.getImageRemote(video_client)
        if nao_image is None:
            print("无法从摄像头获取图像")
            return None

        # 图像转换为 OpenCV 格式
        image_width = nao_image[0]
        image_height = nao_image[1]
        image_array = np.frombuffer(nao_image[6], dtype=np.uint8).reshape((image_height, image_width, 3))
        frame = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
        return frame

    def process_frame(self, frame, obj=None):
        """
        对传入的帧进行 YOLO 目标检测并返回结果
        :param frame: OpenCV 格式的帧
        :return: 检测结果的图像和中心点坐标
        """
        if obj is not None:
            if obj not in self.class_map:
                print(f"未找到对应的物体类别: {obj}")
                return None, None

            obj_class = self.class_map[obj]  # 获取类别索引
            results = self.model.predict(source=frame,  # 传递每一帧图像
                                        conf=0.25,     # 置信度阈值
                                        iou=0.45,      # IoU 阈值
                                        classes=[obj_class], # 指定只检测的类别
                                        device='cpu',   # 使用 CPU 或 GPU 进行推理
                                        save=False,     # 不保存结果
                                        show=False)     # 不展示图像

            processed_frame = results[0].plot()  # 获取带有检测框的图像

            # 使用 .numel() 检查是否有检测结果
            if results[0].boxes.xyxy.numel() > 0:  # 如果检测到物体
                box = results[0].boxes.xyxy[0]  # 获取第一个物体的边界框
                x1, y1, x2, y2 = box[:4]  # 左上角和右下角的坐标 (x1, y1, x2, y2)
                center_x = (x1 + x2) / 2  # 计算中心点的 x 坐标
                center_y = (y1 + y2) / 2  # 计算中心点的 y 坐标
                return processed_frame, (center_x.item(), center_y.item())  # 返回处理后的图像和中心点元组 (x, y)

            return processed_frame, None  # 如果没有检测到物体，返回 None
        return frame, None