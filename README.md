# PhiAutoRender

PhiAutoRender 是一个基于 Python 的自动化渲染 Phigros 谱面的工具。

使用 GPL-3.0 许可证开源。


## 功能
- 自动下载 Phigros Apk
- 自动解包
- 支持识别新歌曲、追加AT、改谱三大更新
- 自动构建 MD5 表，极速识别更新内容
- 自动渲染
- 自动生成视频封面
- 自动上传到 Bilibili

## 开始使用

### 0. 先决条件

- Python 3.10 及以上版本
- Git
- [Phi-Recorder](https://github.com/2278535805/Phi-Recorder) 1.5.0 及以上版本

> [!IMPORTANT]  
> 请确保使用 Phi-Recorder 1.5.0 及以上版本，否则可能无法正确渲染。Phi-Recorder 1.5.0 版本修改了输出文件命令行参数，使用旧版本会导致 Upload 模块无法识别。

- [Motrix](https://motrix.app/)

### 1. 克隆仓库
```bash
git clone https://github.com/Dehou23333-awa/PhiAutoRender.git
cd PhiAutoRender
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置

创建 .env 文件，并根据 .env.example 填写内容。

有关 bilibili 配置，请参考 [bilibili-api-python 文档](https://nemo2011.github.io/bilibili-api/#/get-credential)

### 4. 运行
```bash
python main.py
```

## 声明
本项目仅供学习交流使用，请勿用于商业用途。请勿将本项目内的任何资源进行二次分发。

本项目与 Phigros 官方无任何关联。

本项目不保证任何功能的可用性和稳定性，使用过程中出现的任何问题与本项目无关。

使用本项目即视为同意以上声明。

# 参考项目
- [Phigros Resource by 7aGiven](https://github.com/7aGiven/Phigros_Resource/)
- [Phi Recorder by HLMC](https://github.com/2278535805/Phi-Recorder/)
- [Resource Auto by HLMC](https://github.com/2278535805/Resource_Auto/)