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
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv'}

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

def upload_to_oss(file_path, bucket):
    """上传文件到OSS"""
    original_name = os.path.basename(file_path)
    # 生成随机文件名
    object_name = generate_random_filename(original_name)
    bucket.put_object_from_file(object_name, file_path)
    return f"https://anderson-video.oss-cn-chengdu.aliyuncs.com/{object_name}"

def main():
    parser = argparse.ArgumentParser(description='视频上传OSS工具')
    parser.add_argument('archive', help='文件夹路径')
    parser.add_argument('-o', '--output', default='video_links.csv', help='CSV输出路径')
    parser.add_argument('--endpoint', required=True, help='OSS Endpoint')
    parser.add_argument('--bucket-name', required=True, help='OSS Bucket名称')
    parser.add_argument('--access-key-id', required=True, help='ACCESS_KEY_ID')
    parser.add_argument('--access-key-secret', required=True, help='ACCESS_KEY_SECRET')
    args = parser.parse_args()

    # 初始化OSS
    auth = oss2.Auth(args.access_key_id, args.access_key_secret)
    bucket = oss2.Bucket(auth, args.endpoint, args.bucket_name)

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
            oss_url = upload_to_oss(video, bucket)
            # 获取文件名（不包含扩展名）
            video_name = Path(video.name).stem
            writer.writerow([video_name, oss_url])
            print(f"已上传 {video_name}")
        print("上传完成")

if __name__ == '__main__':
    main()