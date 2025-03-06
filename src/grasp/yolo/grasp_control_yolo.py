import qi
import sys
import time
import cv2
# from yolo_detection import YOLODetection
# import grasp_ground_position
# import grasp_table_position
from .yolo_detection import YOLODetection
from . import grasp_ground_position
from . import grasp_table_position


# 全局字典用于存储摄像头的检测结果
result = {
    'center_top': None,
    'center_bottom': None,
}

def disable_autonomous_life(session):
    """
    禁用NAO机器人的自主能力（Autonomous Life）
    """
    autonomous_life_service = session.service("ALAutonomousLife")
    autonomous_life_service.setState("disabled")

def make_nao_stand(motion_service, posture_service):
    """
    让NAO机器人站起来
    """
    motion_service.wakeUp()
    posture_service.goToPosture("StandInit", 0.5)

def move_to_position(motion_service, angle):
    """
    让机器人按照指定角度进行旋转
    """
    motion_service.moveTo(0, 0, angle)

def reset_head_position(motion_service):
    """
    将头部角度复位到初始位置
    """
    motion_service.setAngles("HeadYaw", 0.0, 0.2)

def execute_rough_logic(motion_service, center_top):
    """
    当目标距离较远时的行走逻辑
    """
    x = center_top[0]

    # 动态旋转和前进
    if x < 300:
        print("目标靠左，左转")
        motion_service.moveTo(0.3, 0, 0.2)  # 左转
    elif x > 340:
        print("目标靠右，右转")
        motion_service.moveTo(0.3, 0, -0.2)  # 右转
    else:
        print("目标在中间位置，向前移动")
        motion_service.moveTo(0.3, 0, 0)  # 向前移动

    time.sleep(0.1)

def execute_careful_logic(motion_service, center_bottom):
    """
    当目标距离较近时的行走逻辑
    """
    print("执行下摄像头行走逻辑")

    tx = 342
    ty = 360
    x = center_bottom[0]
    y = center_bottom[1]
    print("x,y:",x,y)
    # 计算 x 和 y 偏移量
    dx = 0  # 水平方向的调整值
    dy = 0  # 垂直方向的调整值

    # X方向的调整
    if x < 200:
        dx = 0.1  # 左移
    elif x > 450:
        dx = -0.08  # 右移
    elif 200 <= x <= tx - 10:
        dx = 0.01  # 小步左移
    elif tx + 10 <= x <= 450:
        dx = -0.02  # 小步右移

    # Y方向的调整
    if y < 180:
        dy = 0.2  # 前进
    elif y < ty - 15:
        dy = 0.01  # 小步前进
    elif y > ty + 15:
        dy = -0.02  # 后退

    # 执行同时在 x 和 y 方向上的移动
    print(f"移动参数: 前后: {dy}, 左右: {dx}")
    motion_service.moveTo(dy, dx, 0)  # 同时在前后和左右方向上调整
    time.sleep(0.1)

def execute_puttarget_logic(motion_service, center_bottom):
    x = center_bottom[0]
    y = center_bottom[1]
    print("x,y:",x,y)
    # 计算 x 和 y 偏移量
    dx = 0  # 水平方向的调整值
    dy = 0  # 垂直方向的调整值

    # X方向的调整
    if x < 200:
        dx = 0.1  # 左移
    elif x > 450:
        dx = -0.08  # 右移

    # Y方向的调整
    if y < 300:
        dy = 0.2  # 前进

    # 执行同时在 x 和 y 方向上的移动
    print(f"移动参数: 前后: {dy}, 左右: {dx}")
    motion_service.moveTo(dy, dx, 0)  # 同时在前后和左右方向上调整
    time.sleep(0.1)


# def process_table(yolo_detector, video_service, video_client, motion_service, obj):
#     """
#     封装桌子上的操作逻辑（table）。
#     """
#     print("执行桌子上的操作流程（table）...")
#     head_angle = 0.0  # 初始头部角度
#     head_step = 0.2  # 每次转动的角度
#     head_min_angle = -1.5  # 头部最左边的角度
#     head_max_angle = 1.5  # 头部最右边的角度
#     direction = 1  # 初始转头方向
#     while True:
#         # 从上摄像头获取图像
#         frame = yolo_detector.get_nao_camera_frame(video_service, video_client)
#         if frame is None:
#             print("摄像头未成功捕获图像")
#         else:
#             print("摄像头图像捕获成功")

#         # 进行 YOLO 目标检测
#         processed_frame, center = yolo_detector.process_frame(frame, obj=obj)

#         if center:
#             print("检测到桌子上的目标中心点: ", center)

#             reset_head_position(motion_service)
#             motion_service.moveTo(0, 0, head_angle)
#             head_angle = 0.0
#             tx = 342
#             ty = 360

#             x, y = center[0], center[1]

#             # 判断目标是否在指定的范围内
#             if abs(x - tx) <= 10 and abs(y - ty) <= 15:
#                 print(f"目标在范围内，开始抓取: x={x}, y={y}")
#                 grasp_table_position.grasp_table_actions(session)
#                 break  # 退出循环


#             else:
#                 execute_careful_logic(motion_service, center)
#                 # continue
#         else:
#             print("未检测到目标，开始转头寻找")
#             head_angle += direction * head_step
#             if head_angle > head_max_angle or head_angle < head_min_angle:
#                 direction *= -1  # 改变方向
#                 head_angle += direction * head_step  # 修正角度到有效范围内
#             motion_service.setAngles("HeadYaw", head_angle, 0.2)

#         # 显示处理后的帧
#         cv2.imshow("YOLO Table Detection", processed_frame)

#         # 按下 'q' 键退出
#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             break

#         time.sleep(0.03)


def process_table(session, yolo_detector, video_service, top_video_client, bottom_video_client, motion_service, obj):
    """
    封装桌子上的操作逻辑（table）。
    """
    print("执行桌子上的操作流程（table）...")
    head_angle = 0.0  # 初始头部角度
    head_step = 0.2  # 每次转动的角度
    head_min_angle = -1.5  # 头部最左边的角度
    head_max_angle = 1.5  # 头部最右边的角度
    direction = 1  # 初始转头方向

    while True:
        # 1. 先用下摄像头获取图像
        frame = yolo_detector.get_nao_camera_frame(video_service, bottom_video_client)
        if frame is None:
            continue

        # 进行 YOLO 目标检测
        processed_frame, center = yolo_detector.process_frame(frame, obj=obj)

        if not center:
            print("下摄像头未检测到目标，切换到上摄像头...")
            # 2. 切换到上摄像头获取图像
            frame = yolo_detector.get_nao_camera_frame(video_service, top_video_client)
            if frame is None:
                continue

            # 进行 YOLO 目标检测
            processed_frame, center = yolo_detector.process_frame(frame, obj=obj)

            if center:
                print("上摄像头检测到目标，执行移动操作...")
                reset_head_position(motion_service)
                motion_service.moveTo(0, 0, head_angle)
                head_angle = 0.0
                execute_rough_logic(motion_service, center) 
            else:
                print("未检测到目标，开始转头寻找")
                head_angle += direction * head_step
                if head_angle > head_max_angle or head_angle < head_min_angle:
                    direction *= -1  # 改变方向
                    head_angle += direction * head_step  # 修正角度到有效范围内
                motion_service.setAngles("HeadYaw", head_angle, 0.2)
        else:
            # print("下摄像头检测到目标，执行精细定位操作...")
            print(f"下摄像头检测到目标，坐标: {center}")
            reset_head_position(motion_service)
            motion_service.moveTo(0, 0, head_angle)
            head_angle = 0.0
            tx = 342
            ty = 360

            x, y = center[0], center[1]

            # 判断目标是否在指定的范围内
            if abs(x - tx) <= 10 and abs(y - ty) <= 15:
                print(f"目标在范围内，开始抓取: x={x}, y={y}")
                grasp_table_position.grasp_table_actions(session)
                break  # 退出循环
            else:
                execute_careful_logic(motion_service, center)

        # 显示处理后的帧
        cv2.imshow("YOLO Table Detection", processed_frame)
        # 按下 'q' 键退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    time.sleep(0.03)


def process_ground(session, yolo_detector, video_service, top_video_client, bottom_video_client, motion_service, obj):
    """
    封装地上操作的逻辑（ground）。
    """

    print("执行地上的操作流程（ground）...")
    head_angle = 0.0  # 初始头部角度
    head_step = 0.2  # 每次转动的角度
    head_min_angle = -1.5  # 头部最左边的角度
    head_max_angle = 1.5  # 头部最右边的角度
    direction = 1  # 初始转头方向

    while True:
        # 1. 先用下摄像头获取图像
        frame = yolo_detector.get_nao_camera_frame(video_service, bottom_video_client)
        if frame is None:
            continue

        # 进行 YOLO 目标检测
        processed_frame, center = yolo_detector.process_frame(frame, obj=obj)

        if not center:
            print("下摄像头未检测到目标，切换到上摄像头...")
            # 2. 切换到上摄像头获取图像
            frame = yolo_detector.get_nao_camera_frame(video_service, top_video_client)
            if frame is None:
                continue

            # 进行 YOLO 目标检测
            processed_frame, center = yolo_detector.process_frame(frame, obj=obj)

            if center:
                print("上摄像头检测到目标，执行移动操作...")
                reset_head_position(motion_service)
                motion_service.moveTo(0, 0, head_angle)
                head_angle = 0.0
                motion_service.setAngles("HeadPitch", 0.5235987755982988, 0.1)
                execute_rough_logic(motion_service, center) 
            else:
                print("未检测到目标，开始转头寻找")
                head_angle += direction * head_step
                if head_angle > head_max_angle or head_angle < head_min_angle:
                    direction *= -1  # 改变方向
                    head_angle += direction * head_step  # 修正角度到有效范围内
                motion_service.setAngles("HeadYaw", head_angle, 0.2)
        else:
            # print("下摄像头检测到目标，执行精细定位操作...")
            print(f"下摄像头检测到目标，坐标: {center}")
            reset_head_position(motion_service)
            motion_service.moveTo(0, 0, head_angle)
            head_angle = 0.0
            tx = 342
            ty = 360

            x, y = center[0], center[1]

            # 判断目标是否在指定的范围内
            if abs(x - tx) <= 10 and abs(y - ty) <= 15:
                print(f"目标在范围内，开始抓取: x={x}, y={y}")
                grasp_ground_position.grasp_ground_actions(session)
                break  # 退出循环
            else:
                motion_service.setAngles("HeadPitch", 0.5235987755982988, 0.1)
                execute_careful_logic(motion_service, center)

        # 显示处理后的帧
        cv2.imshow("YOLO Table Detection", processed_frame)
        # 按下 'q' 键退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    time.sleep(0.03)


def place_target(session, yolo_detector, video_service, top_video_client, bottom_video_client, motion_service):
    """
    封装放置到target的操作逻辑。
    """
    motion_service.moveTo(0, 0, 1.5708)
    print("放置到指定地点...")
    head_angle = 0.0  # 初始头部角度
    head_step = 0.2  # 每次转动的角度
    head_min_angle = -1.5  # 头部最左边的角度
    head_max_angle = 1.5  # 头部最右边的角度
    direction = 1  # 初始转头方向

    while True:
        # 1. 先用下摄像头获取图像
        frame = yolo_detector.get_nao_camera_frame(video_service, bottom_video_client)
        if frame is None:
            continue

        # 进行 YOLO 目标检测
        processed_frame, center = yolo_detector.process_frame(frame, "target")

        if not center:
            print("下摄像头未检测到目标，切换到上摄像头...")
            # 2. 切换到上摄像头获取图像
            frame = yolo_detector.get_nao_camera_frame(video_service, top_video_client)
            if frame is None:
                continue

            # 进行 YOLO 目标检测
            processed_frame, center = yolo_detector.process_frame(frame, "target")

            if center:
                print("上摄像头检测到目标，执行移动操作...")
                reset_head_position(motion_service)
                motion_service.moveTo(0, 0, head_angle)
                head_angle = 0.0
                motion_service.setAngles("HeadPitch", 0.5235987755982988, 0.1)
                execute_rough_logic(motion_service, center) 
            else:
                print("未检测到目标，开始转头寻找")
                head_angle += direction * head_step
                if head_angle > head_max_angle or head_angle < head_min_angle:
                    direction *= -1  # 改变方向
                    head_angle += direction * head_step  # 修正角度到有效范围内
                motion_service.setAngles("HeadYaw", head_angle, 0.2)
        else:
            # print("下摄像头检测到目标，执行精细定位操作...")
            print(f"下摄像头检测到目标，坐标: {center}")
            reset_head_position(motion_service)
            motion_service.moveTo(0, 0, head_angle)
            head_angle = 0.0
            x, y = center[0], center[1]

            # 判断目标是否在指定的范围内
            if x > 300 and y >200 and y<450 :
                print(f"目标在范围内，开始放置: x={x}, y={y}")
                grasp_ground_position.make_nao_reached(session)
                break  # 退出循环
            else:
                motion_service.setAngles("HeadPitch", 0.5235987755982988, 0.1)
                execute_puttarget_logic(motion_service, center)
                
        # 显示处理后的帧
        cv2.imshow("YOLO Table Detection", processed_frame)
        # 按下 'q' 键退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    time.sleep(0.03)


def main(session, location, obj):
    """
    执行主逻辑
    """
    # 获取服务
    motion_service = session.service("ALMotion")
    video_service = session.service("ALVideoDevice")
    posture_service = session.service("ALRobotPosture")

    # 初始化 YOLO 检测类，加载 YOLO 模型
    yolo_detector = YOLODetection(model_path='/home/zcy/project/ultralytics/runs/train/exp/weights/best.pt')

    # 订阅摄像头
    top_camera_id = 0
    bottom_camera_id = 1
    resolution = 2  # 640x480 分辨率
    color_space = 11  # RGB 颜色空间
    fps = 30  # 帧率

    # 订阅摄像头服务
    top_video_client = video_service.subscribeCamera("top_video_client", top_camera_id, resolution, color_space, fps)
    bottom_video_client = video_service.subscribeCamera("bottom_video_client", bottom_camera_id, resolution, color_space, fps)

    # 禁用自主能力
    disable_autonomous_life(session)
    make_nao_stand(motion_service, posture_service)
    
    try:
        if location == "table":
            # 执行桌子上的操作逻辑
            process_table(session, yolo_detector, video_service, top_video_client, bottom_video_client, motion_service, obj)
            place_target(session, yolo_detector, video_service, top_video_client, bottom_video_client, motion_service)
        elif location == "ground":
            # 执行地上的操作逻辑
            motion_service.setAngles("HeadPitch", 0.5235987755982988, 0.1)
            process_ground(session, yolo_detector, video_service, top_video_client, bottom_video_client, motion_service, obj)
            place_target(session, yolo_detector, video_service, top_video_client, bottom_video_client, motion_service)
        else:
            print("未指定有效的 location")

    finally:
        # 取消订阅摄像头
        video_service.unsubscribe(top_video_client)
        video_service.unsubscribe(bottom_video_client)
        cv2.destroyAllWindows()

if __name__ == "__main__":
    session = qi.Session()
    try:
        session.connect("tcp://172.20.10.9:9559")
        print("成功连接到 NAO 机器人")
    except RuntimeError as e:
        print(f"无法连接到 NAO 机器人: {e}")
        sys.exit(1)

    # 假设抓取位置是 "table"，物品是 "yellowball"
    main(session, location="ground", obj="pinkball")



