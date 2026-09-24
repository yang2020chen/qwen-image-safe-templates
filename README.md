# Qwen-Image-2.1 Safe Latent Grid 自动化模板套件与工程规范

> **针对 ComfyUI 官方 Issue #16435 的工业级避坑指南与高信噪比生产模板**  
> 适配硬件：AMD Radeon RX 7900 XTX 24GB (ROCm 7.2) / NVIDIA RTX 4090 / RTX 3060 等  
> 服务端：ComfyUI (默认 `http://192.168.0.110:8188`)

---

## 1. 核心问题背景与根因（Issue #16435）

### 1.1 经典灾难现象（Deep-fried Artifacts）
在进行 Qwen-Image-2.1 局部重绘（Inpainting / Edit Anything）或参考图迁移（Reference Transfer）时，经常会遇到极具破坏性的画质崩塌：
- **画面过锐化与重度油画感**：原图清透自然的摄影级皮肤变成像粗糙油画或铅笔素描一样的质感；
- **严重彩色噪波与大面积黑斑**：四肢、锁骨及面部边缘出现密密麻麻的焦黑斑块；
- **全图背景严重漂移碎石化**：原本干净的工作室或极简微水泥背景被强行重绘成破裂石块或模糊泥泞；
- **指令部分失效**：即使 Prompt 中反复强调 `preserve background, preserve identity`，模型依然全图胡乱重绘。

### 1.2 根因剖析（RoPE 频域共振干涉）
该现象并非硬件算力、ROCm 驱动或模型权重问题，而是 **ComfyUI 核心处理参考图时的 Latent 网格重采样算法与 3D-RoPE（Rotary Position Embedding）位置编码脱节** 导致的：
1. 当向 `TextEncodeQwenImage21` 传入参考图时，节点内部会根据传入的 `resolution` 参数，将原图按面积等效缩放；
2. 如果此时传入 `resolution = 0`（默认保留原图比例），或者外部传入的 `EmptyLatentImage` 画布尺寸与重采样后的实际参考图 Latent 网格不一致（例如画布传了 `1376 × 1824`，但模型参考图被拉伸为非标准网格）；
3. 模型的 3D-RoPE 旋转位置编码在自注意力层发生剧烈的高频谐振，导致模型无法区分“原图空间基准”与“待生成空间”，产生全图重绘和过饱和油画黑斑灾难。

### 1.3 黄金避坑铁律（Safe Latent Grid Rule）
- **单图编辑 / 多图参考场景**：
  - 必须将 `TextEncodeQwenImage21` 的 `resolution` 严格锁定为 **`1056`**！
  - 必须将 `EmptyLatentImage` 画布尺寸根据原图宽高比严格计算为对应的 **安全网格尺寸（Safe Latent Grid）**，确保 1:1 绝对对齐！
- **纯文生图场景（T2I，不接参考图）**：
  - 不经过 reference-latent 重采样，可直接放开至原生 2K（如 `1376 × 1824` 竖版、`1824 × 1216` 横版、`1536 × 1536` 方形），此时 `TextEncodeQwenImage21` 的 `resolution` 设为对应长边（1824 / 1536）即可。

---

## 2. 安全网格换算公式与速查表

### 2.1 换算公式
给定任意参考原图的宽度 $W_{orig}$ 与高度 $H_{orig}$，安全网格计算规则如下：
$$\text{ratio} = \frac{W_{orig}}{H_{orig}}$$
$$\text{Safe Width} = \operatorname{round}\left(\frac{\sqrt{1056^2 \times \text{ratio}}}{32}\right) \times 32$$
$$\text{Safe Height} = \operatorname{round}\left(\frac{\sqrt{1056^2 / \text{ratio}}}{32}\right) \times 32$$

### 2.2 常见比例换算速查表
| 画面比例 | 原图常见尺寸参考 | 推荐 EmptyLatent 尺寸 | TextEncode resolution | 等效像素 | 适用场景 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1:1 方形** | 1024 × 1024 / 2048 × 2048 | **`1056 × 1056`** | **1056** | ~1.12 MP | 方形肖像、产品展示、Logo 图标 |
| **3:4 竖版** | 1024 × 1365 / 1376 × 1824 | **`928 × 1216`** | **1056** | ~1.13 MP | 人物全身/半身换装、商业海报 |
| **4:3 横版** | 1365 × 1024 / 1824 × 1376 | **`1216 × 928`** | **1056** | ~1.13 MP | 群像合照、横屏展示、桌面壁纸 |
| **9:16 竖屏** | 1080 × 1920 / 720 × 1280 | **`768 × 1408`** | **1056** | ~1.08 MP | 抖音/小红书/Shorts 移动端全屏 |
| **16:9 宽屏** | 1920 × 1080 / 2560 × 1440 | **`1408 × 768`** | **1056** | ~1.08 MP | 电影级横屏大景、水榭漫步 |
| **纯文生图 2K** | （无参考图输入） | **`1376 × 1824`** | **1824** | ~2.51 MP | 原生高写实微距、宋体杂志排版 |

> **提示**：可直接在终端中运行内置网格换算工具快速计算：
> ```bash
> python qwen_safe_pipeline.py calc-grid --width 1080 --height 1920
> ```

---

## 3. 模板套件目录结构

本模板库同时沉淀了 **API 自动化格式** 与 **Web UI 前端拖拽格式**，并已同步部署至远端 110 服务器：

```text
qwen_image_safe_templates/
├── README.md                      # 本说明文档
├── qwen_safe_pipeline.py          # 自动化 Python SDK & 命令行工具
├── generate_templates.py          # 模板工程批量生成器
├── api/                           # 面向 Python / HTTP API 调用的标准 JSON
│   ├── 01_safe_edit_text.json
│   ├── 02_safe_edit_ref.json
│   ├── 03_safe_t2i_portrait_2k.json
│   ├── 04_safe_t2i_landscape_2k.json
│   ├── 05_safe_character_pose.json
│   ├── 06_safe_commercial_ad.json
│   ├── 07_safe_rgba_transparent.json
│   └── 08_safe_multiref_group.json
└── web/                           # 面向 ComfyUI 浏览器界面直接 Load 的可视工作流
    ├── 01_safe_edit_text_web.json
    ├── 02_safe_edit_ref_web.json
    ├── 03_safe_t2i_portrait_2k_web.json
    ├── 04_safe_t2i_landscape_2k_web.json
    ├── 05_safe_character_pose_web.json
    ├── 06_safe_commercial_ad_web.json
    ├── 07_safe_rgba_transparent_web.json
    └── 08_safe_multiref_group_web.json
```

---

## 4. 8 大核心场景与模板速查

### 01. 单图纯文本局部换装与局部重绘 (`01_safe_edit_text`)
- **工作流文件**：`web/01_safe_edit_text_web.json`
- **核心逻辑**：采用空心红圈（Hollow Red Outline）标定待编辑区域，其余区域由 1056 安全网格 100% 像素级锁死。
- **网格配置**：`EmptyLatent: 928 × 1216`, `resolution: 1056`
- **Prompt 语法**：
  ```text
  Use <image1> as the canvas for the person, pose, composition, and background, and edit only the clothing area enclosed by the red outline. Replace the casual sweater with a tailored charcoal-grey Italian wool blazer, fitted white silk shirt underneath, delicate fabric texture, and realistic textile folds. Remove the red outline from the final result. Preserve the subject's face, skin, hair, and clean modern studio background from <image1> exactly unchanged.
  ```

### 02. 双图物料参考精准换装 (`02_safe_edit_ref`)
- **工作流文件**：`web/02_safe_edit_ref_web.json`
- **核心逻辑**：`<image1>` 作为模特姿势与背景画布，`<image2>` 作为高级成衣面料与纹样参考。
- **网格配置**：`EmptyLatent: 928 × 1216`, `resolution: 1056`
- **Prompt 语法**：
  ```text
  Use <image1> as the canvas for the person, pose, composition, and background, and edit only the clothing area enclosed by the red outline. Use <image2> as the reference for the garment design, colors, delicate embroidery patterns, and fabric materials, completely replacing the original clothing with the luxury haute couture tweed dress from <image2>. Accurately adapt the dress to the standing pose, including natural folds and realistic shadows. Completely remove the red outline. Preserve the model's identity, facial features, crystal-clear cold white skin tone, hairstyle, and modern studio background from <image1> exactly unchanged.
  ```

### 03. 原生 2K 竖版高写实肖像 (`03_safe_t2i_portrait_2k`)
- **工作流文件**：`web/03_safe_t2i_portrait_2k_web.json`
- **核心逻辑**：纯文生图极限 2.51MP，无参考图干涉。呈现次表面散射（SSS）凝脂肤质与超自然细微发丝。
- **网格配置**：`EmptyLatent: 1376 × 1824`, `resolution: 1824`

### 04. 原生 2K 横版大景与严苛杂志排版 (`04_safe_t2i_landscape_2k`)
- **工作流文件**：`web/04_safe_t2i_landscape_2k_web.json`
- **核心逻辑**：检验模型对中英双语宋体字、西文字体字形及版面留白的排版渲染能力。
- **网格配置**：`EmptyLatent: 1824 × 1216`, `resolution: 1824`

### 05. 设定集/三视图驱动的动态姿态重绘 (`05_safe_character_pose`)
- **工作流文件**：`web/05_safe_character_pose_web.json`
- **核心逻辑**：输入角色正面/侧面/背面三视图，生成新姿势下（水榭漫步回眸）全身大景，面部与服装 100% 保持一致。
- **网格配置**：`EmptyLatent: 1824 × 1216`, `resolution: 1056`

### 06. 商业广告人货焦散与握持交互 (`06_safe_commercial_ad`)
- **工作流文件**：`web/06_safe_commercial_ad_web.json`
- **核心逻辑**：精准解耦右手手指骨骼与切面水晶香水瓶的咬合关系，真实模拟液体焦散与琥珀色高光在手部皮肤上的投射。
- **网格配置**：`EmptyLatent: 928 × 1216`, `resolution: 1056`

### 07. 原生 4 通道 RGBA 资产直出 (`07_safe_rgba_transparent`)
- **工作流文件**：`web/07_safe_rgba_transparent_web.json`
- **核心逻辑**：直接生成原生带透明 Alpha 通道的吹制水晶鹤与青烟，背景为完全透明，免去抠图绿幕。
- **网格配置**：`EmptyLatent: 1536 × 1536`, `resolution: 1536`

### 08. 极限 10 图并发群像合照 (`08_safe_multiref_group`)
- **工作流文件**：`web/08_safe_multiref_group_web.json`
- **核心逻辑**：同时接入 10 位异域肖像图，一次性在圣托里尼露台上生成 10 人合影，各人脸特征严格对应且不混淆。
- **网格配置**：`EmptyLatent: 1216 × 928`, `resolution: 1056`

---

## 5. 三种生产调用方式

### 方式一：ComfyUI 浏览器 Web UI 原生拖拽使用
1. 打开浏览器访问 `http://192.168.0.110:8188`；
2. 点击右侧工具栏的 **Workflows -> Browse**；
3. 直接选择 `01_safe_edit_text_web` ~ `08_safe_multiref_group_web` 中任意模板，点击加载即可；
4. 模板中已内置彩色模块分组（蓝色模型区、粉色安全网格区、绿色提示词区、橙色输出区），直接修改 Prompt 与输入图片即可点击 **Queue** 运行。

### 方式二：Python SDK 编程与自动化批处理
在 Python 脚本中引入 SDK，即可实现毫秒级网格对齐与全自动推理：
```python
from qwen_safe_pipeline import QwenSafePipeline

client = QwenSafePipeline(server_url="http://192.168.0.110:8188")

# 1. 纯文本空心红圈换装
result = client.edit_anything_text(
    input_image="/path/to/model_red_outline.png",
    prompt="Replace the clothes with a luxury navy silk cheongsam.",
    output_path="./output_cheongsam.png"
)
print(f"Done in {result['elapsed']}s! Saved to {result['path']}")

# 2. 双图物料参考换装
result = client.edit_with_reference(
    canvas_image="/path/to/model_red_outline.png",
    reference_image="/path/to/couture_dress.png",
    prompt="Completely replace clothes with reference dress.",
    output_path="./output_couture.png"
)

# 3. 原生 2K 文生图
result = client.generate_t2i_2k(
    prompt="Extreme portrait of an East Asian woman, 8k, photorealistic...",
    output_path="./output_portrait.png",
    orientation="portrait"  # or 'landscape', 'square'
)
```

### 方式三：CLI 命令行直接调用
无需编写代码，通过终端命令行一步生成：
```bash
# 检查 GPU 与显存状态
python qwen_safe_pipeline.py health

# 换算安全网格尺寸
python qwen_safe_pipeline.py calc-grid --width 1024 --height 1365

# 一键执行文本局部编辑
python qwen_safe_pipeline.py edit-text \
  --canvas /Volumes/web_studio/test_results/aesthetic_benchmark_v2/v2_base_beauty_hollow_red.png \
  --prompt "Replace clothes with a bespoke charcoal wool blazer. Remove red outline. Preserve skin and background." \
  --output ./my_result.png

# 执行预置模板并覆盖种子
python qwen_safe_pipeline.py run-template \
  --template 01_safe_edit_text \
  --output ./template_out.png \
  --seed 999999
```

---

## 6. 硬件配置与实测性能指标

在远程 110 主机（AMD Radeon RX 7900 XTX 24GB + ROCm 7.2）上的实测数据：

| 测试场景 | 空 latent 尺寸 | 采样步数 | 显存峰值占用 | 单步耗时 (s/it) | 总出图耗时 | 画质与稳定性 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **单图编辑 (928×1216)** | 928 × 1216 | 32 steps | 17.8 GB | **1.53 s/it** | **49.2 秒** | 零黑斑、零油画感、微水泥背景 100% 锁死 |
| **双图物料参考 (928×1216)** | 928 × 1216 | 35 steps | 18.2 GB | **1.57 s/it** | **55.1 秒** | 欧根纱半透光影完美、零噪波 |
| **纯文生图 2K (1376×1824)** | 1376 × 1824 | 32 steps | 19.5 GB | **2.88 s/it** | **92.4 秒** | SSS 凝脂肤质微距、8K 毛孔毛绒感 |
| **纯文生图 2K (1824×1216)** | 1824 × 1216 | 32 steps | 19.4 GB | **2.85 s/it** | **91.8 秒** | 杂志级宋体与西文零错字排版 |
| **极限 10 图并发群像** | 1216 × 928 | 35 steps | 21.1 GB | **1.97 s/it** | **69.8 秒** | 吞吐 ~2 万 Vision Tokens，零 OOM |

**模型组合配置推荐**：
- **UNet**：`qwen_image_2.1_int8_convrot.safetensors`
- **CLIP**：`qwen3vl_8b_w4a8.safetensors`
- **VAE**：`qwen_image_2.1_vae_bf16.safetensors`
