---
name: qwen-image-safe-studio
description: Qwen-Image-2.1 Safe Latent Grid 自动化生图与局部精准换装/重绘工作流。一键执行纯文生图、空心红圈局部精准换装（自动连袖全包标定、1056安全网格换算防崩、真实语义Prompt重写）与多图参考迁移，直连本地或远程 110 ComfyUI 服务器全自动出图。
---

# Qwen-Image-2.1 Safe Latent Studio 自动化生图与换装技能

## 一、技能定位与使命

本 Skill 旨在将 **Qwen-Image-2.1** 繁琐的实机生图、尺寸对齐与局部重绘全流程封装为**完全自动化的开箱即用工作流**：
- **终结手动算尺寸**：自动套用 $W, H = \operatorname{round}\left(\frac{\sqrt{1056^2 \times \text{ratio}}}{32}\right) \times 32$，彻底根除 ComfyUI Issue #16435 导致的过锐化、大面积黑斑与全图碎石化；
- **终结手动画红圈**：内置 `mark_outline.py` 几何标定引擎，支持一键生成“连袖全包、下摆齐整”的精准闭合空心红圈，杜绝手臂断裂与薄纱溢出；
- **终结提示词翻车**：自动执行真实语义对齐（描述底图真实衣物而非凭空捏造），注入五官、皮肤与背景 100% 锁死守护语句；
- **全自动直连出图**：直连本地或远程 ComfyUI API（默认 `http://127.0.0.1:8188`，支持 `--server` 参数或环境变量 `COMFY_URL` 动态覆盖），纯 HTTP REST 自动上传底图、提交任务、轮询监控并拉取无损原图。

---

## 二、快速开箱即用（Turn-Key CLI）

所有核心功能已封装在配套脚本 [pipeline.py](./scripts/pipeline.py) 与 [mark_outline.py](./scripts/mark_outline.py) 中：

### 1. 场景 A：一键文生图（生成干净主角底图）
```bash
python .agents/skills/qwen-image-safe-studio/scripts/pipeline.py t2i \
  --prompt "Full-body fashion portrait of a stunning East Asian woman, wearing a fitted cream knit sweater and navy pleated skirt. Minimalist gallery background, soft sunlight, 8k resolution." \
  --width 928 \
  --height 1216 \
  --output ./base_protagonist.png
```

### 2. 场景 B：一键“仅替换上衣”（全自动标定+换装）
自动在底图上生成符合人体工学的连袖封闭红圈，将上衣精准替换为新服装，下半身与面部 100% 锁死：
```bash
python .agents/skills/qwen-image-safe-studio/scripts/pipeline.py edit-top \
  --image ./base_protagonist.png \
  --prompt "Use <image1> as the canvas for the person, pose, composition, and background, and edit only the clothing area enclosed by the red outline. Completely replace the original cream-white ribbed knit sweater with a sharply tailored charcoal-grey Italian wool blazer, structured shoulders, white silk shirt underneath. Remove the red outline from the final result. Preserve the subject's face, neck, skin tone, hair, hands, navy-blue pleated skirt, bare legs, and gallery background from <image1> exactly unchanged." \
  --output ./edited_top_only.png
```

### 3. 场景 C：自定义红圈局部重绘（Edit Anything）
针对用户自己绘制了红圈标定的任意底图，自动换算 1056 安全网格并执行推理：
```bash
python .agents/skills/qwen-image-safe-studio/scripts/pipeline.py edit \
  --image ./my_custom_red_marked_canvas.png \
  --prompt "Use <image1> as the canvas... edit only the area enclosed by the red outline..." \
  --output ./edit_result.png
```

### 4. 场景 D：安全网格尺寸速算（防崩计算器）
输入任意原图尺寸，秒级换算符合 ComfyUI RoPE 规则的无损 EmptyLatent 画布尺寸：
```bash
python .agents/skills/qwen-image-safe-studio/scripts/pipeline.py calc-grid --width 1080 --height 1920
# 输出: Original: 1080x1920 -> 1056 Safe Grid: 768x1408
```

---

## 三、四大核心避坑铁律（必须严格遵循）

### 铁律 1：1056 安全网格换算（Issue #16435 防崩法则）
- **单图编辑 / 多图参考场景**：
  - `TextEncodeQwenImage21` 的 `resolution` 参数**必须且只能锁定为 `1056`**！
  - `EmptyLatentImage` 画布尺寸必须根据原图宽高比 $\text{ratio} = W / H$ 严格换算为：
    $$W_{safe} = \operatorname{round}\left(\frac{\sqrt{1056^2 \times \text{ratio}}}{32}\right) \times 32, \quad H_{safe} = \operatorname{round}\left(\frac{\sqrt{1056^2 / \text{ratio}}}{32}\right) \times 32$$
  - 严禁传入任意截图尺寸（如 `906 × 1191`），非标尺寸会导致扩散潜空间插值高频共振，全图糙化碎石化。

### 铁律 2：红圈标定“连袖全包、下摆齐整”物理边界
- **严禁肢体截断**：如果要替换上衣/外套，红线必须将**领口、双肩、前胸、手臂以及完整袖口（Wrist Cuffs）全包在红圈内**。
- **原因**：模型收到“红圈外严格保留”的死命令，若将手臂袖子露在红圈外，模型会强行在外套袖子外拼接原图的袖子，造成脏黑色薄纱或异化肢体。

### 铁律 3：Prompt 真实语义咬合（杜绝幻觉描述）
- **必须真实描述原图衣物**：
  - ✅ **正确**：`Completely replace the original cream-white ribbed knit sweater with a tailored charcoal blazer...`
  - ❌ **错误**：底图明明是毛衣，却写 `Replace the casual dress...`（注意力散焦，引发脸部和领口混乱）。
- **必须声明消除红圈与锁死区域**：
  - 必须包含：`Remove the red outline from the final result.`
  - 必须包含：`Preserve the subject's face, skin, hair, [lower_garment], legs, and clean studio background from <image1> exactly unchanged.`

### 铁律 4：杜绝多代截图噪波累积（Feedback Loop Error Compounding）
- 必须使用上一轮生成的无损原始 PNG（如 `928 × 1216`），禁止直接使用系统网页截图（带有色彩压缩与显示器非整数缩放）。在 `denoise = 1.0` 采样下，截图微噪波会被剧烈放大导致腿部与墙面出现红黄斑驳。

---

## 四、安全网格尺寸速查表 (Safe Latent Grid Cheatsheet)

| 画面比例 | 典型原图分辨率 | 推荐 EmptyLatent 尺寸 | TextEncode resolution | 适用业务场景 |
| :--- | :--- | :--- | :--- | :--- |
| **1:1 方形** | 1024 × 1024 / 2048 × 2048 | **`1056 × 1056`** | **1056** | 方形肖像、珠宝/香水静物微距、图标 |
| **3:4 竖版** | 1024 × 1365 / 1376 × 1824 | **`928 × 1216`** | **1056** | **人物半身/全身换装、电商模特出街、海报** |
| **4:3 横版** | 1365 × 1024 / 1824 × 1376 | **`1216 × 928`** | **1056** | 多人合影、横屏特写、博客宽幅配图 |
| **9:16 竖屏** | 1080 × 1920 / 720 × 1280 | **`768 × 1408`** | **1056** | 抖音、小红书、YouTube Shorts 全屏移动物料 |
| **16:9 宽屏** | 1920 × 1080 / 2560 × 1440 | **`1408 × 768`** | **1056** | 电影级横屏大景、水榭游廊动态漫步 |
| **纯文生图 2K** | （无参考图输入） | **`1376 × 1824` / `1824 × 1216`** | **1824** | 原生微距凝脂微毛孔肤质、宋体排版大片 |

---

## 五、ComfyUI 执行环境与节点配置标准

服务端接入：默认 `http://127.0.0.1:8188`（支持通过环境变量 `export COMFY_URL="http://<server-ip>:8188"` 或 `--server` 命令行参数指定任意远程服务器）。无需配置 SSH。
- **UNet**：`qwen_image_2.1_int8_convrot.safetensors`
- **CLIP**：`qwen3vl_8b_w4a8.safetensors`（type: `qwen_image`）
- **VAE**：`qwen_image_2.1_vae_bf16.safetensors`
- **TextEncodeQwenImage21**：
  - 编辑场景：输入连 `clip`、`vae`，动态插槽连 `images.image_1`，`resolution = 1056`
  - 文生图场景：仅连 `clip`，省略 `vae`，`resolution = 1824`
- **KSampler**：`steps: 32`, `cfg: 1.0`, `sampler: euler`, `scheduler: simple`, `denoise: 1.0`
