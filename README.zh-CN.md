# s3-image-process

本项目使用 FastAPI 实现了一个 API，用于处理存储在 S3 存储桶中的图片，支持调整大小、裁剪、添加水印、自动旋转和质量变换等功能。同时还支持多种文档格式之间的转换。

## 项目结构

```
.
├── server/
│   ├── main.py
│   ├── image_processor.py
│   ├── image_cropper.py
│   ├── s3_operations.py
│   ├── image_watermark.py
│   ├── image_format_converter.py
│   ├── image_auto_orient.py
│   ├── image_quality.py
│   ├── doc_converter.py
│   ├── doc_processor.py
│   ├── doc_service.py
│   ├── ddb_operations.py
│   ├── font/
│   │   └── 华文楷体.ttf
│   ├── requirements.txt
│   └── Dockerfile
├── cloudformation.yaml
├── .gitignore
└── README.md
```

## 部署说明

### 本地开发部署

1. 进入服务器目录：
   ```
   cd server
   ```

2. 创建虚拟环境：
   ```
   python -m venv venv
   ```

3. 激活虚拟环境：
   - Windows系统：
     ```
     venv\Scripts\activate
     ```
   - macOS 和 Linux系统：
     ```
     source venv/bin/activate
     ```

4. 安装依赖包：
   ```
   pip install -r requirements.txt
   ```

5. 配置AWS凭证：
   - 在`server`目录下创建`.env`文件
   - 添加AWS凭证和S3存储桶信息：
     ```
     S3_BUCKET_NAME=your_bucket_name
     ```

6. 运行FastAPI服务器：
   ```
   uvicorn main:app --reload
   ```

服务器将在`http://127.0.0.1:8000`上运行。您可以在`http://127.0.0.1:8000/docs`访问API文档。

## API使用说明

API提供了统一的图片处理和文档转换端点，支持操作链式调用：

### 图片处理端点

```
/image/{image_key}?operations=operation1,param1_value1/operation2,param1_value1,param2_value2
```

### 文档处理端点

```
/doc/{document_key}?operations=convert,source_{format},target_{format},pages_{base64pages}
```

### 文档转换功能

#### 支持的源文件格式：

1. Word文档：
   - doc, docx, wps, wpss, docm, dotm, dot, dotx, html

2. PPT文档：
   - pptx, ppt, pot, potx, pps, ppsx, dps, dpt, pptm, potm, ppsm, dpss

3. Excel文档：
   - xls, xlt, et, ett, xlsx, xltx, csv, xlsb, xlsm, xltm, ets

4. PDF文档：
   - pdf

#### 支持的目标格式：

- PDF：将任何支持的格式转换为PDF
- PNG/JPG：将任何支持的格式转换为图片
- TXT：从Word、PowerPoint和PDF文档中提取文本

#### 功能特点：

1. 页面选择：
   - 使用base64编码的页码转换指定页面
   - 示例："1,2,4-10"（需要进行base64编码）

2. 输出文件命名：
   - 无页面选择时：原文件名.{目标格式}
   - 有页面选择时：原文件名_p{页码}.{目标格式}
   示例：
   - document.docx → document.pdf
   - document.docx（第1,2,3页）→ document_p1_2_3.pdf

3. 质量控制：
   - 高质量PDF转换
   - 可配置的图像DPI（默认：300）
   - 优化的图像质量设置

#### 使用示例：

```bash
# 将DOCX转换为PDF（所有页面）
curl -X GET "http://127.0.0.1:8000/doc/document.docx?operations=convert,target_pdf"

# 将DOCX的特定页面转换为PDF（第1,2,3页）
# 注意：页码需要进行base64编码
curl -X GET "http://127.0.0.1:8000/doc/document.docx?operations=convert,target_pdf,pages_MSwyLDM"

# 将DOCX转换为PNG
curl -X GET "http://127.0.0.1:8000/doc/document.docx?operations=convert,target_png"

# 从PDF提取文本
curl -X GET "http://127.0.0.1:8000/doc/document.pdf?operations=convert,target_txt"
```

### 使用示例

#### 1. 基本操作

测试每个独立操作：

```
# 自动旋转测试
http://127.0.0.1:8000/image/example.jpg?operations=auto-orient,1

# 调整大小测试（原始大小的50%）
http://127.0.0.1:8000/image/example.jpg?operations=resize,p_50

# 裁剪测试（从中心裁剪800x600）
http://127.0.0.1:8000/image/example.jpg?operations=crop,w_800,h_600,g_center

# 水印测试
http://127.0.0.1:8000/image/example.jpg?operations=watermark,text_Q29weXJpZ2h0,g_se,t_80

# 质量测试（80%质量）
http://127.0.0.1:8000/image/example.jpg?operations=quality,q_80
```

#### 2. 链式操作

组合多个转换操作的复杂示例：

```
# 链式操作1：自动旋转 + 调整大小 + 质量压缩
http://127.0.0.1:8000/image/example.jpg?operations=auto-orient,1/resize,w_800,h_600/quality,q_85

# 链式操作2：调整大小 + 裁剪 + 水印
http://127.0.0.1:8000/image/example.jpg?operations=resize,p_70/crop,w_800,h_600,g_center/watermark,text_Q29weXJpZ2h0,g_se

# 链式操作3：自动旋转 + 裁剪 + 水印 + 质量压缩
http://127.0.0.1:8000/image/example.jpg?operations=auto-orient,1/crop,w_800,h_600,g_center/watermark,text_Q29weXJpZ2h0,g_se/quality,q_85

# 链式操作4：调整大小 + 水印 + 质量压缩
http://127.0.0.1:8000/image/example.jpg?operations=resize,w_1200,h_800/watermark,text_Q29weXJpZ2h0,g_se,t_80/quality,q_90

# 链式操作5：组合所有操作
http://127.0.0.1:8000/image/example.jpg?operations=auto-orient,1/resize,p_70/crop,w_800,h_600,g_center/watermark,text_Q29weXJpZ2h0,g_se,t_80/quality,q_85
```

## API参数说明

### 操作：auto-orient（自动旋转）

- 参数值：自动旋转模式
  - `0`：保持原始方向（默认）
  - `1`：根据EXIF数据自动旋转

示例：`auto-orient,1`

注意：如果原始图片没有EXIF方向数据，自动旋转操作将不会产生效果。

### 操作：resize（调整大小）

- `p`：按比例缩放的百分比（1-1000）
- `w`：目标宽度
- `h`：目标高度
- `m`：调整大小模式
  - `lfit`：适应指定尺寸（默认）
  - `mfit`：最小适应
  - `fill`：填充并裁剪
  - `pad`：填充透明背景
  - `fixed`：强制指定尺寸

### 操作：crop（裁剪）

- `w`：裁剪宽度
- `h`：裁剪高度
- `x`：X轴偏移（默认：0）
- `y`：Y轴偏移（默认：0）
- `g`：裁剪基准点
  - `nw`：左上
  - `north`：正上
  - `ne`：右上
  - `west`：左中
  - `center`：正中
  - `east`：右中
  - `sw`：左下
  - `south`：正下
  - `se`：右下
- `p`：裁剪后的缩放百分比（1-200，默认：100）

### 操作：watermark（水印）

- `text`：Base64编码的水印文字（支持UTF-8，包括中文）
  - 示例："Hello World" 应编码为 "SGVsbG8gV29ybGQ"
  - 中文文字 "版权所有" 应编码为 "54mI5p2D5omA5pyJ"
- `t`：透明度（0-100，默认：100）
- `g`：位置（nw, north, ne, west, center, east, sw, south, se；默认：se）
- `x`：水平偏移（0-4096，默认：10）
- `y`：垂直偏移（0-4096，默认：10）
- `voffset`：中心对齐时的垂直偏移（-1000到1000，默认：0）
- `fill`：是否填充水印（0或1，默认：0）
- `padx`：水印之间的水平间距（0-4096，默认：0）
- `pady`：水印之间的垂直间距（0-4096，默认：0）
- `size`：字体大小（可选，默认自动计算）

### 操作：quality（质量变换）

- 参数：
  - `q`：相对质量参数（1-100）
    - 按指定百分比对图片进行质量压缩
    - 适用于JPG格式的相对质量调整
    - 对于WebP格式，效果等同于绝对质量参数
  - `Q`：绝对质量参数（1-100）
    - 设置固定的质量值
    - 仅支持JPG和WebP格式
    - 当原图质量高于目标质量时，压缩至目标质量
    - 当原图质量低于目标质量时，保持原图质量不变

注意：必须指定相对质量(q)或绝对质量(Q)其中之一，不能同时使用。

使用示例：
```bash
# 使用相对质量参数（压缩到80%）
curl -X GET "http://127.0.0.1:8000/image/example.jpg?operations=quality,q_80" --output result.jpg

# 使用绝对质量参数（设置为90）
curl -X GET "http://127.0.0.1:8000/image/example.jpg?operations=quality,Q_90" --output result.jpg

# 与其他操作链式调用
curl -X GET "http://127.0.0.1:8000/image/example.jpg?operations=resize,w_800/quality,q_85" --output result.jpg
```

### 水印功能特点

1. 中文文字支持：
   - 内置支持中文字符（使用华文楷体.ttf）
   - 清晰可读的文字渲染
   - 基于图片尺寸的自动字体大小调整
   - 支持Base64编码的文字输入以确保正确的字符处理

2. 增强可见度：
   - 半透明背景提升对比度
   - 优化文字不透明度
   - 增加文字周围填充
   - 默认大小为图片较小边长的1/20

3. 最佳实践：
   - 始终使用Base64编码水印文字
   - 使用默认透明度（t=100）获得最佳清晰度
   - 避开图片繁忙区域（默认g=se）
   - 对于小图片或文字不清晰时，可指定更大的size参数
   - 使用简洁的文字提高可读性

## 缓存机制

API实现了缓存头以提高性能：

- `Cache-Control: public, max-age=3600`：允许缓存处理后的图片1小时
- `ETag`：为每个处理后的图片提供唯一标识符，实现高效的缓存验证

## 清理

要删除此堆栈创建的所有资源，可以从CloudFormation控制台或使用AWS CLI删除堆栈。

## 注意

本README假设您在本地运行服务器。对于生产环境部署，请将`http://127.0.0.1:8000`替换为您实际的API端点URL。
