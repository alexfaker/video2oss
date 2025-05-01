# 视频上传 OSS 工具

## 功能说明

将压缩包中的视频文件自动上传至阿里云 OSS，并生成包含下载链接的 CSV 文件

## 环境要求

- Python 3.6+
- 依赖库：`oss2`

## 快速开始

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 运行脚本（参数示例）
python video_upload_oss.py /path/to/videos.zip \
  --access-key-id YOUR_ACCESS_KEY_ID \
  --access-key-secret YOUR_ACCESS_KEY_SECRET \
  --endpoint oss-cn-hangzhou.aliyuncs.com \
  --bucket-name your-bucket-name \
  -o output.csv




```
