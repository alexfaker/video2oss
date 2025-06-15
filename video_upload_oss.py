#!/usr/bin/env python3
import os
import argparse
import zipfile
import tarfile
import csv
import oss2
from pathlib import Path
import hashlib
import time
import random

# 支持的视频格式
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv','.png','.jpg','.jpeg','.gif','.webp'}

def extract_archive(archive_path, extract_dir):
    """解压压缩文件"""
    if zipfile.is_zipfile(archive_path):
        with zipfile.ZipFile(archive_path) as zf:
            for file in zf.namelist():
                # 跳过 macOS 的 ._ 前缀文件
                if file.startswith('__MACOSX/') or file.endswith('/._'):
                    continue
                try:
                    # 直接使用原始文件名
                    zf.extract(file, extract_dir)
                except Exception as e:
                    print(f"解压文件 {file} 时出错: {str(e)}")
    elif tarfile.is_tarfile(archive_path):
        with tarfile.open(archive_path) as tf:
            tf.extractall(extract_dir)
    else:
        raise ValueError("Unsupported archive format")

def find_videos(directory):
    """递归查找视频文件"""
    video_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            # 跳过 macOS 的 ._ 前缀文件
            if file.startswith('._'):
                continue
            if Path(file).suffix.lower() in VIDEO_EXTENSIONS:
                video_files.append(Path(root) / file)
    return video_files

def format_folder_path(folder):
    """格式化文件夹路径"""
    if not folder:
        return ""
    # 确保文件夹路径以'/'结尾
    return folder.rstrip('/') + '/'

def check_folder_exists(bucket, folder_path):
    """检查OSS文件夹是否存在"""
    if not folder_path:
        return True  # 根目录始终存在
    
    try:
        # 检查文件夹下是否有任何对象
        result = bucket.list_objects(prefix=folder_path, max_keys=1)
        return len(result.object_list) > 0
    except Exception as e:
        print(f"检查文件夹时出错: {str(e)}")
        return False

def generate_random_filename(original_name):
    """生成随机文件名"""
    # 获取当前时间戳
    timestamp = int(time.time())
    # 生成随机数
    random_num = random.randint(1000, 9999)
    # 使用原始文件名生成哈希值
    hash_obj = hashlib.md5(original_name.encode('utf-8'))
    hash_value = hash_obj.hexdigest()[:8]
    # 获取文件扩展名
    ext = Path(original_name).suffix
    # 组合成新的文件名
    return f"{timestamp}_{random_num}_{hash_value}{ext}"

def upload_to_oss(file_path, bucket, folder_path=""):
    """上传文件到OSS"""
    original_name = os.path.basename(file_path)
    # 生成随机文件名
    random_filename = generate_random_filename(original_name)
    object_name = folder_path + random_filename
    bucket.put_object_from_file(object_name, file_path)
    return f"https://{object_name}.oss-cn-chengdu.aliyuncs.com/{object_name}"

def main():
    parser = argparse.ArgumentParser(description='视频上传OSS工具')
    parser.add_argument('archive', help='文件夹路径')
    parser.add_argument('-o', '--output', default='video_links.csv', help='CSV输出路径')
    parser.add_argument('--folder', default='', help='OSS bucket中的目标文件夹路径')
    parser.add_argument('--endpoint', required=True, help='OSS Endpoint')
    parser.add_argument('--bucket-name', required=True, help='OSS Bucket名称')
    parser.add_argument('--access-key-id', required=True, help='ACCESS_KEY_ID')
    parser.add_argument('--access-key-secret', required=True, help='ACCESS_KEY_SECRET')
    args = parser.parse_args()

    # 初始化OSS
    auth = oss2.Auth(args.access_key_id, args.access_key_secret)
    bucket = oss2.Bucket(auth, args.endpoint, args.bucket_name)
    
    # 处理文件夹路径
    folder_path = format_folder_path(args.folder)
    
    # 检查文件夹是否存在
    if folder_path and not check_folder_exists(bucket, folder_path):
        print(f"错误：OSS文件夹 '{args.folder}' 不存在")
        print("请先在OSS控制台或通过其他工具创建该文件夹，然后重新运行脚本")
        print(f"建议操作：")
        print(f"1. 登录阿里云OSS控制台")
        print(f"2. 进入bucket '{args.bucket_name}'")
        print(f"3. 创建文件夹 '{args.folder}'")
        return

    # 查找视频文件
    video_files = find_videos(args.archive)
    if not video_files:
        print("未找到视频文件")
        return

    # 上传并记录
    with open(args.output, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['视频名称', 'OSS链接'])
        
        for video in video_files:
            oss_url = upload_to_oss(video, bucket, folder_path)
            # 获取文件名（不包含扩展名）
            video_name = Path(video.name).stem
            writer.writerow([video_name, oss_url])
            print(f"已上传 {video_name}")
        print("上传完成")

if __name__ == '__main__':
    main()