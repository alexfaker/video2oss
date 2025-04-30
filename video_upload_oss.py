#!/usr/bin/env python3
import os
import argparse
import zipfile
import tarfile
import csv
import oss2
from pathlib import Path

# 支持的视频格式
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv'}

def extract_archive(archive_path, extract_dir):
    """解压压缩文件"""
    if zipfile.is_zipfile(archive_path):
        with zipfile.ZipFile(archive_path) as zf:
            zf.extractall(extract_dir)
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
            if Path(file).suffix.lower() in VIDEO_EXTENSIONS:
                video_files.append(Path(root) / file)
    return video_files

def upload_to_oss(file_path, bucket):
    """上传文件到OSS"""
    object_name = os.path.basename(file_path)
    bucket.put_object_from_file(object_name, file_path)
    return f"https://{bucket.bucket_name}.{bucket.endpoint}/{object_name}"

def main():
    parser = argparse.ArgumentParser(description='视频上传OSS工具')
    parser.add_argument('archive', help='压缩文件路径')
    parser.add_argument('-o', '--output', default='video_links.csv', help='CSV输出路径')
    parser.add_argument('--endpoint', required=True, help='OSS Endpoint')
    parser.add_argument('--bucket-name', required=True, help='OSS Bucket名称')
    parser.add_argument('--access-key-id', required=True, help='ACCESS_KEY_ID')
    parser.add_argument('--access-key-secret', required=True, help='ACCESS_KEY_SECRET')
    args = parser.parse_args()

    # 初始化OSS
    auth = oss2.Auth(args.access_key_id, args.access_key_secret)
    bucket = oss2.Bucket(auth, args.endpoint, args.bucket_name)

    # 解压文件
    extract_dir = Path(args.archive).stem + '_extracted'
    extract_archive(args.archive, extract_dir)

    # 查找视频文件
    video_files = find_videos(extract_dir)
    if not video_files:
        print("未找到视频文件")
        return

    # 上传并记录
    with open(args.output, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['视频名称', 'OSS链接'])
        
        for video in video_files:
            oss_url = upload_to_oss(video, bucket)
            writer.writerow([video.name, oss_url])
            print(f"已上传 {video.name}")

if __name__ == '__main__':
    main()