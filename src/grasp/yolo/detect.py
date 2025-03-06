# -*- coding: utf-8 -*-
import warnings
warnings.filterwarnings('ignore')
from ultralytics import YOLO

if __name__ == '__main__':

    # 加载模型
    model = YOLO(model=r'/home/zcy/project/ultralytics/runs/train/exp2/weights/best.pt')  # 使用训练后的模型

    # 进行批量预测，对整个文件夹的图片进行检测
    model.predict(source=r'/home/zcy/project/src/dataset/images/val',  # 传递文件夹路径
                  save=True,  # 保存预测结果
                  show=False,  # 显示检测图像
                  conf=0.25,  # 置信度阈值
                  iou=0.45,   # IoU 阈值
                  device='cpu'  # 使用 CPU 或 GPU 进行推理
                  )