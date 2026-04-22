import cv2
import os
import re

def images_to_video(image_folder, output_video_path, fps=30):
    """
    将文件夹下的图片按顺序合并为视频
    
    :param image_folder: 存放图片的文件夹路径
    :param output_video_path: 输出视频的文件路径（如 'output.mp4'）
    :param fps: 视频的帧率（默认30帧/秒）
    """
    
    # 检查文件夹是否存在
    if not os.path.exists(image_folder):
        print(f"错误: 文件夹 '{image_folder}' 不存在。")
        return
        
    # 获取文件夹中所有支持的图片文件
    valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp')
    images = [img for img in os.listdir(image_folder) if img.lower().endswith(valid_extensions)]
    
    if not images:
        print(f"错误: 文件夹 '{image_folder}' 中没有找到支持的图片文件。")
        return

    # 提取文件名中的数字进行排序（如果文件名包含数字，如 img_1.jpg, img_2.jpg）
    # 如果纯粹按字符串排序可能会导致 img_10 排在 img_2 前面
    def natural_sort_key(s):
        return [int(text) if text.isdigit() else text.lower()
                for text in re.split(r'(\d+)', s)]
                
    images.sort(key=natural_sort_key)
    
    print(f"找到 {len(images)} 张图片，开始处理...")
    
    # 读取第一张图片来获取视频的分辨率（宽度和高度）
    first_image_path = os.path.join(image_folder, images[0])
    frame = cv2.imread(first_image_path)
    
    if frame is None:
        print(f"错误: 无法读取第一张图片 '{first_image_path}'。")
        return
        
    height, width, layers = frame.shape
    
    # 定义视频编码器和创建 VideoWriter 对象
    # 'mp4v' 是 mp4 格式的常用编码器
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
    
    # 逐张读取图片并写入视频
    for i, image_name in enumerate(images):
        img_path = os.path.join(image_folder, image_name)
        frame = cv2.imread(img_path)
        
        # 确保所有图片的尺寸与第一张相同
        if frame.shape[:2] != (height, width):
            frame = cv2.resize(frame, (width, height))
            
        video.write(frame)
        
        # 打印进度
        if (i + 1) % 10 == 0 or (i + 1) == len(images):
            print(f"进度: {i + 1}/{len(images)} 帧已写入...")

    # 释放资源
    cv2.destroyAllWindows()
    video.release()
    print(f"\n合并完成！视频已保存至: {output_video_path}")

if __name__ == "__main__":
    # ========== 配置区域 ==========
    
    # 1. 存放图片的文件夹路径（请修改为您自己的文件夹路径）
    # 比如 r"D:\Project\face_vue\images"
    IMAGE_FOLDER = r"./images" 
    
    # 2. 输出视频的路径和名称
    OUTPUT_VIDEO = r"./output.mp4"
    
    # 3. 视频帧率 (FPS) - 数值越大，视频播放越快，一般视频为 24 或 30
    FPS = 30
    
    # ==============================
    
    # 如果文件夹不存在，给出一个友好的提示并创建一个测试用的空文件夹
    if not os.path.exists(IMAGE_FOLDER):
        os.makedirs(IMAGE_FOLDER)
        print(f"已创建示例文件夹 '{IMAGE_FOLDER}'，请将图片放入该文件夹后再次运行本脚本。")
    else:
        images_to_video(IMAGE_FOLDER, OUTPUT_VIDEO, FPS)