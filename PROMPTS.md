# Qwen-Image-2.1 开源生图提示词全集 (Open Prompts Catalog)

> **项目仓库**：[yang2020chen/qwen-image-safe-templates](https://github.com/yang2020chen/qwen-image-safe-templates)  
> **基准运行硬件**：AMD Radeon RX 7900 XTX 24GB (ROCm 7.2) / NVIDIA RTX 4090  
> **ComfyUI 规范**：锁定 CFG = 1.0 · 单图/多图编辑 TextEncode resolution 锁定 1056 · 画布 EmptyLatent 锁定 1056 安全网格

本清单收录了 **Qwen-Image-2.1 Safe Studio** 实测 10 大战役、5 套基准母体物料及 8 套可视化模板的全部开源 Prompt 提示词与配套生成参数。可直接复制至 ComfyUI 或通过自动化脚本调用。

---

## 目录
1. [10 大标杆战役实战提示词](#1-10-大战役实战提示词)
   - [战役 01: 微距写实肖像 (2K SSS 凝脂肤质)](#战役-01-微距写实肖像-2k-sss-凝脂肤质)
   - [战役 02: 中英文宋体排版 (东方留白 美学新生)](#战役-02-中英文宋体排版-东方留白-美学新生)
   - [战役 03: 严苛个位数计数 (1壶 3盏 1炉 2花)](#战役-03-严苛个位数计数-1壶-3盏-1炉-2花)
   - [战役 04A: 纯文本空心红圈换装 (深灰高级西装)](#战役-04a-纯文本空心红圈换装-深灰高级西装)
   - [战役 04B: 双图物料参考迁移 (高定小香风洋装)](#战役-04b-双图物料参考迁移-高定小香风洋装)
   - [战役 05: 三视图驱动动态漫步回眸 (水榭长廊)](#战役-05-三视图驱动动态漫步回眸-水榭长廊)
   - [战役 06: 商业广告人货焦散 (奢华水晶香水瓶)](#战役-06-商业广告人货焦散-奢华水晶香水瓶)
   - [战役 07: 满月荷塘夜景重绘 (冷暖双轮廓光)](#战役-07-满月荷塘夜景重绘-冷暖双轮廓光)
   - [战役 08: 原生 4 通道 RGBA 资产直出 (吹制琉璃鹤)](#战役-08-原生-4-通道-rgba-资产直出-吹制琉璃鹤)
   - [战役 09: 10 位异域肖像并发群像 (圣托里尼露台)](#战役-09-10-位异域肖像并发群像-圣托里尼露台)
   - [战役 10: 超现实解剖级融合 (琉璃蝶翼仙女)](#战役-10-超现实解剖级融合-琉璃蝶翼仙女)
2. [5 套基准母体物料提示词](#2-5-套基准母体物料提示词)
3. [Qwen-Image-2.1 提示词语法与避坑黄金法则](#3-qwen-image-21-提示词语法与避坑黄金法则)

---

## 1. 10 大战役实战提示词

### 战役 01: 微距写实肖像 (2K SSS 凝脂肤质)
- **模式**：T2I (文生图)
- **推荐尺寸**：`1376 × 1824`（3:4 竖版 2K）
- **采样参数**：Steps 32~35, CFG 1.0, Sampler `euler`, Scheduler `simple`
- **成果大图**：[`01_test_macro_realism_2k.png`](assets/01_test_macro_realism_2k.png)
- **Prompt (英文)**：
```text
A breathtaking 2K high-fashion beauty portrait of an East Asian supermodel. Extreme close-up shot capturing her mesmerizing gaze, authentic translucent porcelain skin texture with microscopic visible pores, delicate peach fuzz along the cheekbone, authentic tear film reflections in her dark eyes, and soft natural lip crevices with subtle hydration gloss. She wears an architectural high-collar black cashmere top. Warm morning directional rim lighting pouring from the top left, creating a cinematic falloff with genuine depth of field. Masterpiece ultra-photorealistic editorial quality, zero plastic smoothing, zero artificial artifacts.
```
- **核心要点**：强调 `microscopic visible pores`, `peach fuzz`, `translucent porcelain skin`, 彻底杜绝塑料假面磨皮感。

---

### 战役 02: 中英文宋体排版 (东方留白 美学新生)
- **模式**：T2I (文生图)
- **推荐尺寸**：`1376 × 1824` 或 `1824 × 1216`
- **采样参数**：Steps 32~35, CFG 1.0
- **成果大图**：[`02_test_typography_bilingual_2k.png`](assets/02_test_typography_bilingual_2k.png)
- **Prompt (英文)**：
```text
A high-end editorial fashion magazine cover photograph featuring an East Asian supermodel with sculpted cheekbones and bold red lips. Across the top edge, large bold elegant serif English letters read "ORIENTAL HAUTE COUTURE" with letters perfectly spaced. Along the right side, a vertical column of refined Chinese Songti typography reads "浮光掠影 · 东方织造" followed by a smaller subtitle "传统非遗与现代剪裁的共生实验". In the lower-left corner, clean white barcode graphics and crisp small text read "VOL. 26 / ISSUE 09 · SEPTEMBER 2026". Across the very bottom, small tracked-out sans-serif text reads "SPECIAL EDITION: THE BEAUTY OF JADE". Studio dramatic lighting with deep shadows. All text characters are 100% sharp, perfectly formed, legible, and uncorrupted.
```
- **核心要点**：中文字符用双引号包裹，指定“Chinese Songti typography（宋体）”，排版字距与位置明确限定。

---

### 战役 03: 严苛个位数计数 (1壶 3盏 1炉 2花)
- **模式**：T2I (文生图)
- **推荐尺寸**：`1824 × 1216`（3:2 横版）
- **采样参数**：Steps 32, CFG 1.0
- **成果大图**：[`03_test_strict_counting_2k.png`](assets/03_test_strict_counting_2k.png)
- **Prompt (英文)**：
```text
A 2K high-angle minimalist zen commercial still-life photograph of a classical Chinese tea ceremony arrangement set upon a dark raw-edge walnut slab table, bathed in soft afternoon window light. The arrangement strictly consists of the following items with exact quantities: On the left side sits exactly one celadon Ru-kiln ceramic teapot with delicate crackle glaze and an arched copper handle. In the exact center of the table are arranged exactly three small translucent mutton-fat white jade teacups, placed in a precise equilateral triangle pattern. On the right side stands exactly one vintage blackened bronze incense burner, with a single slender column of aromatic white smoke curling vertically upward into the air. Resting on the wood in front of the tea cups are exactly two freshly plucked white jasmine blossoms with visible morning dewdrops on their petals. The background is a soft beige washi paper screen with bamboo leaf shadows. Natural diffuse lighting, clean composition, zero extra teacups, teapots, or scattered flowers.
```
- **核心要点**：多次使用 `strictly consists of`, `exactly one/three/two`, 负向声明 `zero extra items`。

---

### 战役 04A: 纯文本空心红圈换装 (深灰高级西装)
- **模式**：Edit (单图参考，红圈区域编辑)
- **输入图**：`<image1>` 带连袖全包封闭红圈的底图（如 `assets/input_references/m1_base_beauty_hollow_red_2k.png`）
- **推荐尺寸**：`928 × 1216` (对齐 1056 安全网格，resolution=1056)
- **采样参数**：Steps 32, CFG 1.0, Denoise 1.0
- **成果大图**：[`04a_test_suit_edit_safe_res1056.png`](assets/04a_test_suit_edit_safe_res1056.png)
- **Prompt (英文)**：
```text
Use <image1> as the canvas for the person, pose, composition, and background, and edit only the clothing area enclosed by the red outline. Completely replace the original clothing with a fitted deep-charcoal professional business suit. The upper garment is a sharply tailored short-sleeve blazer with structured shoulders, narrow lapels, a single-button front, and clearly defined waist darts, worn over a simple ivory silk blouse. Pair it with a matching high-waisted fitted pencil skirt ending above the knees at approximately the same level as the original skirt, fully covering the waist and midriff. Make the clothing conform naturally to the subject’s current pose and anatomy, with realistic suiting texture, seams, folds, fabric tension, environmental shadows, and occlusion. Completely remove the red selection outline from the final result. Preserve the subject’s identity, facial features, expression, skin tone, hairstyle, body proportions, standing pose, arm positions, hands, legs, and bare skin. Preserve the beige studio background, original lighting, shadows, camera angle, composition, and crop. Do not modify any area other than the specified clothing, and do not add jewelry, badges, logos, patterns, or new text.
```
- **核心要点**：必须写明 `edit only the clothing area enclosed by the red outline`，`Completely remove the red selection outline`，并使用 `Preserve ... exactly unchanged` 锁死未被标记的区域。

---

### 战役 04B: 双图物料参考迁移 (高定小香风洋装)
- **模式**：Edit (双图参考，`<image1>` 画布 + `<image2>` 物料)
- **输入图**：`<image1>` 红圈底图，`<image2>` 高定物料图
- **推荐尺寸**：`928 × 1216` (resolution=1056)
- **采样参数**：Steps 35, CFG 1.0
- **成果大图**：[`04b_test_couture_dress_transfer.png`](assets/04b_test_couture_dress_transfer.png)
- **Prompt (英文)**：
```text
Use <image1> as the canvas for the person, pose, composition, and background, and edit only the clothing area enclosed by the red outline. Use <image2> as the reference for the garment design and materials, completely replacing the original clothing in <image1> with the full bespoke pale ice-blue French tweed outfit from <image2>. Accurately adapt the outfit to the woman's current standing pose: fitting the cropped ice-blue tweed jacket with pearl buttons over the ivory ribbed inner camisole, draping the pleated high-waisted skirt around her hips with the delicate waist chain, and letting the sheer translucent chiffon cape hang lightly around her shoulders into airy balloon sleeves. Completely remove the red selection outline from the final result. Preserve the woman's facial identity, skin tone, eyes, hair, standing pose, arms, legs, and the minimalist beige studio background from <image1> completely untouched. Prevent color bleeding onto the skin.
```

---

### 战役 05: 三视图驱动动态漫步回眸 (水榭长廊)
- **模式**：Edit (单图多视角 Character Sheet 参考)
- **输入图**：`<image1>` 三视图设定图 (`m4_character_sheet_2k.png`)
- **推荐尺寸**：`1824 × 1216` (横屏 16:9 大景，resolution=1056)
- **采样参数**：Steps 35, CFG 1.0
- **成果大图**：[`05_test_dynamic_pose_recreation.png`](assets/05_test_dynamic_pose_recreation.png)
- **Prompt (英文)**：
```text
Using the identity, facial features, low chignon hairstyle, and ivory silk dress of the young East Asian woman depicted in <image1>, generate a completely new wide cinematic photograph of her walking gracefully through a traditional Chinese lakeside pavilion corridor at twilight. She is captured in dynamic mid-stride, turning her head back over her shoulder with an elegant, gentle gaze towards the camera. Her silk dress and hair wisps gently billow in the soft evening breeze. In the background, the serene lotus pond mirrors the deep indigo twilight sky and glowing silk lanterns hung beneath curved wood pavilion eaves. Natural cinematographic lighting, authentic motion and atmosphere, with her facial identity perfectly matching all three views in <image1>.
```

---

### 战役 06: 商业广告人货焦散 (奢华水晶香水瓶)
- **模式**：Edit (双图参考，人脸/姿态 + 货品材质)
- **输入图**：`<image1>` 模特图，`<image2>` 香水瓶参考图
- **推荐尺寸**：`928 × 1216` (resolution=1056)
- **采样参数**：Steps 32~35, CFG 1.0
- **成果大图**：[`06_test_commercial_perfume_ad.png`](assets/06_test_commercial_perfume_ad.png)
- **Prompt (英文)**：
```text
Use <image1> as the reference for the East Asian woman's facial identity, skin tone, hair, and elegant poise. Use <image2> as the reference for the luxury perfume bottle's faceted crystal glass, amber liquid, and gold atomizer. Compose a high-end luxury beauty commercial campaign photograph: the woman is shown in a refined medium close-up, gently cradling the luxury perfume bottle from <image2> between her delicate slender fingers in front of her collarbone. Her soft fingers naturally occlude the side of the glass, while the multifaceted crystal bottle creates authentic refraction, caustics, and amber glows reflecting onto her porcelain skin. The bottle is scaled harmoniously with her hands and torso. Editorial studio three-point lighting, clean minimalist warm-grey background, luxury brand advertising aesthetic.
```

---

### 战役 07: 单图环境重塑与全局重打光 (M1 底图换水榭荷塘夜景)
- **模式**：Edit (单图参考背景重绘与 Relighting)
- **输入图**：`<image1>` 原始母体素材 M1 骨相美人 (`assets/input_references/m1_base_beauty_2k.png`)
- **推荐尺寸**：`928 × 1216` (3:4 安全网格，resolution=1056)
- **采样参数**：Steps 32, CFG 1.0, Denoise 1.0
- **成果大图**：[`07_test_moonlit_lotus_relighting.png`](assets/07_test_moonlit_lotus_relighting.png)
- **Prompt (英文)**：
```text
Use <image1> as the canvas for the person's identity, facial features, porcelain skin tone, hairstyle, and ivory silk dress. Completely replace the minimalist daytime architectural background with an atmospheric classical Chinese water town courtyard at night: a serene dark lotus pond under a deep indigo night sky with a luminous glowing full moon, carved wooden pavilion railings, blooming pink lotus flowers, and warm red silk lanterns casting a gentle glow. Relight the subject naturally according to the new moonlit environment, casting delicate cool silver rim lighting along her hair, shoulders, and silk dress folds, with soft warm amber bounce light from the lanterns reflecting across her skin. Preserve the subject's face, body proportions, and elegant pose from <image1> exactly unchanged, seamless natural composition, masterpiece.
```

---

### 战役 08: 原生 4 通道 RGBA 资产直出 (吹制琉璃鹤)
- **模式**：T2I (带 Alpha 透明通道)
- **推荐尺寸**：`1536 × 1536` (1:1 方形 2K，resolution=1536)
- **采样参数**：Steps 35, CFG 1.0
- **成果大图**：[`08_test_rgba_transparent_crane.png`](assets/08_test_rgba_transparent_crane.png)
- **Prompt (英文)**：
```text
RGBA, isolated on transparent background, alpha channel. A breathtaking art piece of a slender oriental crane made of multi-colored translucent blown crystal glass and glowing neon-amber resin, standing gracefully on a polished 24K gold filigree base. Wisps of delicate, semi-transparent incense smoke spiral softly upward from its slender curved beak, diffusing into thin air. The crystal glass body exhibits intricate internal refraction, rainbow caustics, and pristine optical transparency. The image has a clean alpha channel and a completely transparent background with zero background residue, zero halo, and perfectly smooth anti-aliased glass and semi-transparent smoke edges.
```
- **核心要点**：开头固定引导词 `RGBA, isolated on transparent background, alpha channel.`，结尾强调 `completely transparent background with zero background residue`。

---

### 战役 09: 10 位异域肖像并发群像 (圣托里尼露台)
- **模式**：Edit (10 图并发多参考)
- **输入图**：`<image1>` 至 `<image10>` 10 位独立人脸肖像
- **推荐尺寸**：`1216 × 928` (4:3 横版，resolution=1056)
- **采样参数**：Steps 35, CFG 1.0
- **成果大图**：[`09_test_group_10ref_santorini.png`](assets/09_test_group_10ref_santorini.png)
- **Prompt (英文)**：
```text
A wide cinematic 2K group travel photograph of ten diverse young women taking a memorable vacation photo together in Santorini, Greece. The group features 10 distinct individuals whose facial identities, hairstyles, hair colors, and unique features correspond strictly to: <image1>, <image2>, <image3>, <image4>, <image5>, <image6>, <image7>, <image8>, <image9>, and <image10>. They are arranged naturally in two relaxed tiers on a sun-drenched whitewashed terrace overlooking the azure Aegean sea and iconic blue-domed churches: several women sitting comfortably on the terrace ledge in front, and others standing smiling behind them with natural camaraderie and spontaneous poses. They wear stylish resort summer outfits in crisp white, terracotta, linen, and marine blue. Bright Mediterranean sunlight casts crisp natural shadows. Each of the ten faces is distinct, well-defined, and recognizable from their respective reference image without merging or duplication.
```

---

### 战役 10: 超现实解剖级融合 (琉璃蝶翼仙女)
- **模式**：T2I (文生图)
- **推荐尺寸**：`1536 × 1536` (1:1 方形 2K)
- **采样参数**：Steps 35, CFG 1.0
- **成果大图**：[`10_test_surreal_fairy_wings.png`](assets/10_test_surreal_fairy_wings.png)
- **Prompt (英文)**：
```text
A breathtaking ethereal fantasy fine-art photograph of a graceful celestial fairy maiden floating weightlessly amidst golden-hour sunlit clouds above an ocean of mist. She has delicate porcelain East Asian facial features, eyes gently closed in tranquil meditation, draped in flowing gossamer silk ribbons. Extending seamlessly from her shoulder blades is a pair of magnificent, enormous translucent swallowtail butterfly wings crafted entirely from glowing blown crystal glass and iridescent stained-glass veins. The translucent wing membranes refract the radiant golden sunrise into prismatic rainbow caustics across the surrounding clouds. The anatomical connection between her smooth skin and the crystalline wing roots is seamless and organic, with soft internal luminescence glowing beneath the skin. Masterpiece cinematic volumetric lighting, ethereal and dreamlike.
```

---

## 2. 5 套基准母体物料提示词

复现测试基准所需的 5 类原始物料提示词：

### M1: 东方骨相美人全身底图 (2K: 1376x1824)
```text
A full-length 2K fashion editorial photograph of a graceful and stunning 22-year-old East Asian model standing elegantly in a minimalist sunlit architectural gallery. She has exquisite porcelain skin, delicate facial features, gentle luminous brown almond eyes, soft blush, and long silky jet-black hair tied in a loose low chignon. She is wearing a minimalist, elegant ivory-white mulberry silk camisole dress with delicate spaghetti straps and a subtly flowing flared hem ending below her knees. Her arms rest naturally and gracefully along her sides without crossing or obstructing the dress. The background features a serene warm neutral lime-wash textured gallery wall with soft archway shadows and a tranquil bamboo stalk in the soft-focus distance. Illuminated by soft directional morning sunlight from the left, casting a gentle rim light on her shoulders and authentic translucent subsurface scattering on her skin. High-end editorial fashion atmosphere with ultra-clean composition and pristine 2K clarity.
```

### M2: 高定小香风薄纱披肩洋装物料 (2K: 1376x1824)
```text
A 2K high-fashion studio catalog photograph of a bespoke haute-couture feminine ensemble displayed on a clean matte-white invisible mannequin against a neutral seamless backdrop. The ensemble features: a cropped pale ice-blue French tweed jacket with a round collar, delicate pearl buttons, raw woven fringed trim, and a jeweled floral brooch; a fitted ivory ribbed camisole with ruched bust detailing; a matching ice-blue tweed pleated high-waisted skirt with a slender silver waist chain; and a detachable lightweight translucent pale ice-blue silk chiffon cape that drapes naturally into graceful balloon sleeves and a cascading curved hem. Diffused studio commercial catalog lighting, highlighting the crisp tweed fabric weave, lustrous pearl luster, and sheer airy chiffon layers.
```

### M3: 奢华水晶香水琉璃瓶 (2K: 1536x1536)
```text
A commercial luxury product photograph of an opulent bespoke French perfume bottle centered on a polished dark obsidian stone slab. The bottle is crafted from heavy octagonal multifaceted crystal glass with razor-sharp beveled edges that refract studio light into prismatic rainbow caustics. Inside is a glowing translucent amber fragrance liquid with tiny suspended flecks of 24K pure gold leaf. The bottle neck is adorned with an ornate polished 18K yellow gold atomizer collar and a tied black grosgrain ribbon with metallic gold tips. In the background, soft mist and warm bokeh lights glow gently against a dark charcoal cyclorama. Ultra-sharp macro reflections and crystal clarity.
```

### M4: 角色多视角设定图 Character Sheet (2K: 1536x1536)
```text
A professional 2K character design turnaround model sheet of the same East Asian young woman presented in three distinct angles side-by-side: 1. On the left: a front-facing close-up portrait showing her delicate bone structure, luminous almond eyes, and black low chignon. 2. In the center: a three-quarter 45-degree angle profile capturing her refined jawline, soft gentle expression, and subtle ear jewelry. 3. On the right: a full-body standing pose showing her slender silhouette, posture, and elegant proportions in an ivory silk slip dress. Clean neutral grey studio backdrop with even calibration lighting. Consistent face, consistent hair, consistent identity across all three views.
```

---

## 3. Qwen-Image-2.1 提示词语法与避坑黄金法则

1. **三段式语法结构（针对图生图与编辑）**：
   - **基准画布定界**：`Use <image1> as the canvas for the person, pose, composition, and background, and edit only the [target area] enclosed by the red outline.`
   - **执行与修改声明**：`Completely replace [original] with [new details] from <image2>...`
   - **边界保护与锁死声明**：`Completely remove the red selection outline. Preserve [face, skin, background, lighting] from <image1> exactly unchanged.`

2. **核心参数硬性约束**：
   - **CFG 严禁超过 1.0**：必须保持 `cfg: 1.0`（非 SDXL/Flux 的 3.5~7.0）。
   - **分辨率锁死 1056**：单图编辑/参考迁移时，`TextEncodeQwenImage21` 节点的 `resolution` 参数必须锁定为 `1056`，`EmptyLatentImage` 尺寸必须对齐 1056 安全网格（如 3:4 用 `928 × 1216`）。
   - **红圈连袖全包**：换装时红圈必须将待换上衣的所有衣袖全部框入，杜绝断袖产生拼接伪影。
