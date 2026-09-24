#!/usr/bin/env python3
"""
Generator for Qwen-Image-2.1 Safe Latent Grid Templates (API & Web UI)
Addresses ComfyUI Issue #16435:
- Inpainting / Edit resolution must be locked to 1056
- EmptyLatent dimensions must match safe_grid(w, h, 1056)
"""

import json
import os
import uuid
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
API_DIR = BASE_DIR / "api"
WEB_DIR = BASE_DIR / "web"

API_DIR.mkdir(parents=True, exist_ok=True)
WEB_DIR.mkdir(parents=True, exist_ok=True)

UNET_MODEL = "qwen_image_2.1_int8_convrot.safetensors"
CLIP_MODEL = "qwen3vl_8b_w4a8.safetensors"
VAE_MODEL = "qwen_image_2.1_vae_bf16.safetensors"

# ==============================================================================
# 1. API Template Generators
# ==============================================================================

def make_api_t2i(width=1376, height=1824, steps=32, prompt="", prefix="t2i"):
    return {
        "469": {"class_type": "UNETLoader", "inputs": {"unet_name": UNET_MODEL, "weight_dtype": "default"}},
        "471": {"class_type": "CLIPLoader", "inputs": {"clip_name": CLIP_MODEL, "type": "qwen_image", "device": "default"}},
        "472": {"class_type": "VAELoader", "inputs": {"vae_name": VAE_MODEL}},
        "473": {"class_type": "EmptyLatentImage", "inputs": {"width": width, "height": height, "batch_size": 1}},
        "470": {
            "class_type": "TextEncodeQwenImage21",
            "inputs": {
                "clip": ["471", 0],
                "prompt": prompt,
                "negative_prompt": "",
                "resolution": max(width, height)
            }
        },
        "475": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["469", 0],
                "positive": ["470", 0],
                "negative": ["470", 1],
                "latent_image": ["473", 0],
                "seed": 202609,
                "steps": steps,
                "cfg": 1.0,
                "sampler_name": "euler",
                "scheduler": "simple",
                "denoise": 1.0
            }
        },
        "474": {"class_type": "VAEDecode", "inputs": {"samples": ["475", 0], "vae": ["472", 0]}},
        "494": {"class_type": "SaveImage", "inputs": {"images": ["474", 0], "filename_prefix": prefix}}
    }

def make_api_edit(image_names, width=928, height=1216, resolution=1056, steps=32, prompt="", prefix="edit"):
    graph = {
        "469": {"class_type": "UNETLoader", "inputs": {"unet_name": UNET_MODEL, "weight_dtype": "default"}},
        "471": {"class_type": "CLIPLoader", "inputs": {"clip_name": CLIP_MODEL, "type": "qwen_image", "device": "default"}},
        "472": {"class_type": "VAELoader", "inputs": {"vae_name": VAE_MODEL}},
        "473": {"class_type": "EmptyLatentImage", "inputs": {"width": width, "height": height, "batch_size": 1}},
        "470": {
            "class_type": "TextEncodeQwenImage21",
            "inputs": {
                "clip": ["471", 0],
                "vae": ["472", 0],
                "prompt": prompt,
                "negative_prompt": "",
                "resolution": resolution
            }
        },
        "475": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["469", 0],
                "positive": ["470", 0],
                "negative": ["470", 1],
                "latent_image": ["473", 0],
                "seed": 202609,
                "steps": steps,
                "cfg": 1.0,
                "sampler_name": "euler",
                "scheduler": "simple",
                "denoise": 1.0
            }
        },
        "474": {"class_type": "VAEDecode", "inputs": {"samples": ["475", 0], "vae": ["472", 0]}},
        "494": {"class_type": "SaveImage", "inputs": {"images": ["474", 0], "filename_prefix": prefix}}
    }
    for idx, img in enumerate(image_names, 1):
        nid = str(4800 + idx)
        graph[nid] = {"class_type": "LoadImage", "inputs": {"image": img}}
        graph["470"]["inputs"][f"images.image_{idx}"] = [nid, 0]
    return graph

# ==============================================================================
# 2. Web UI Template Generators (Full ComfyUI Graph Structure)
# ==============================================================================

def make_web_workflow(title, prompt, width, height, resolution=1056, images=None, steps=32, prefix="output"):
    images = images or []
    nodes = []
    links = []
    link_id_counter = 1

    def next_link_id():
        nonlocal link_id_counter
        val = link_id_counter
        link_id_counter += 1
        return val

    # UNetLoader (ID: 469)
    unet_link = next_link_id()
    nodes.append({
        "id": 469,
        "type": "UNETLoader",
        "pos": [100, 100],
        "size": [300, 82],
        "flags": {},
        "order": 0,
        "mode": 0,
        "inputs": [],
        "outputs": [{"name": "MODEL", "type": "MODEL", "links": [unet_link]}],
        "properties": {"Node name for S&R": "UNETLoader"},
        "widgets_values": [UNET_MODEL, "default"]
    })

    # CLIPLoader (ID: 471)
    clip_link = next_link_id()
    nodes.append({
        "id": 471,
        "type": "CLIPLoader",
        "pos": [100, 240],
        "size": [300, 106],
        "flags": {},
        "order": 1,
        "mode": 0,
        "inputs": [],
        "outputs": [{"name": "CLIP", "type": "CLIP", "links": [clip_link]}],
        "properties": {"Node name for S&R": "CLIPLoader"},
        "widgets_values": [CLIP_MODEL, "qwen_image", "default"]
    })

    # VAELoader (ID: 472)
    vae_to_textencode_link = next_link_id() if images else None
    vae_to_decode_link = next_link_id()
    vae_links = [vae_to_decode_link]
    if vae_to_textencode_link:
        vae_links.insert(0, vae_to_textencode_link)

    nodes.append({
        "id": 472,
        "type": "VAELoader",
        "pos": [100, 400],
        "size": [300, 58],
        "flags": {},
        "order": 2,
        "mode": 0,
        "inputs": [],
        "outputs": [{"name": "VAE", "type": "VAE", "links": vae_links}],
        "properties": {"Node name for S&R": "VAELoader"},
        "widgets_values": [VAE_MODEL]
    })

    # EmptyLatentImage (ID: 473)
    latent_link = next_link_id()
    nodes.append({
        "id": 473,
        "type": "EmptyLatentImage",
        "pos": [100, 520],
        "size": [300, 106],
        "flags": {},
        "order": 3,
        "mode": 0,
        "inputs": [],
        "outputs": [{"name": "LATENT", "type": "LATENT", "links": [latent_link]}],
        "properties": {"Node name for S&R": "EmptyLatentImage"},
        "widgets_values": [width, height, 1]
    })

    # LoadImage nodes
    image_links = []
    start_y = 680
    for idx, img_filename in enumerate(images, 1):
        img_link = next_link_id()
        image_links.append((idx, img_link, 4800 + idx))
        nodes.append({
            "id": 4800 + idx,
            "type": "LoadImage",
            "pos": [100 + (idx - 1) * 340, start_y],
            "size": [300, 314],
            "flags": {},
            "order": 4 + idx,
            "mode": 0,
            "inputs": [],
            "outputs": [
                {"name": "IMAGE", "type": "IMAGE", "links": [img_link]},
                {"name": "MASK", "type": "MASK", "links": None}
            ],
            "properties": {"Node name for S&R": "LoadImage"},
            "widgets_values": [img_filename, "image"]
        })

    # TextEncodeQwenImage21 (ID: 470)
    pos_link = next_link_id()
    neg_link = next_link_id()

    text_inputs = [{"name": "clip", "type": "CLIP", "link": clip_link}]
    for idx, lk, _ in image_links:
        text_inputs.append({
            "label": f"image_{idx}",
            "name": f"images.image_{idx}",
            "shape": 7,
            "type": "IMAGE",
            "link": lk
        })
    if images and vae_to_textencode_link:
        text_inputs.append({
            "name": "vae",
            "shape": 7,
            "type": "VAE",
            "link": vae_to_textencode_link
        })

    nodes.append({
        "id": 470,
        "type": "TextEncodeQwenImage21",
        "pos": [480, 100],
        "size": [450, 480],
        "flags": {},
        "order": 10,
        "mode": 0,
        "inputs": text_inputs,
        "outputs": [
            {"name": "positive", "type": "CONDITIONING", "links": [pos_link]},
            {"name": "negative", "type": "CONDITIONING", "links": [neg_link]},
            {"name": "latent", "type": "LATENT", "links": None}
        ],
        "properties": {"Node name for S&R": "TextEncodeQwenImage21"},
        "widgets_values": [prompt, "", resolution]
    })

    # KSampler (ID: 475)
    sample_latent_link = next_link_id()
    nodes.append({
        "id": 475,
        "type": "KSampler",
        "pos": [1000, 100],
        "size": [280, 260],
        "flags": {},
        "order": 11,
        "mode": 0,
        "inputs": [
            {"name": "model", "type": "MODEL", "link": unet_link},
            {"name": "positive", "type": "CONDITIONING", "link": pos_link},
            {"name": "negative", "type": "CONDITIONING", "link": neg_link},
            {"name": "latent_image", "type": "LATENT", "link": latent_link}
        ],
        "outputs": [{"name": "LATENT", "type": "LATENT", "links": [sample_latent_link]}],
        "properties": {"Node name for S&R": "KSampler"},
        "widgets_values": [202609, "randomize", steps, 1.0, "euler", "simple", 1.0]
    })

    # VAEDecode (ID: 474)
    decode_img_link = next_link_id()
    nodes.append({
        "id": 474,
        "type": "VAEDecode",
        "pos": [1340, 100],
        "size": [160, 46],
        "flags": {},
        "order": 12,
        "mode": 0,
        "inputs": [
            {"name": "samples", "type": "LATENT", "link": sample_latent_link},
            {"name": "vae", "type": "VAE", "link": vae_to_decode_link}
        ],
        "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": [decode_img_link]}],
        "properties": {"Node name for S&R": "VAEDecode"},
        "widgets_values": []
    })

    # SaveImage (ID: 494)
    nodes.append({
        "id": 494,
        "type": "SaveImage",
        "pos": [1560, 100],
        "size": [280, 58],
        "flags": {},
        "order": 13,
        "mode": 0,
        "inputs": [{"name": "images", "type": "IMAGE", "link": decode_img_link}],
        "outputs": [{"name": "images", "type": "IMAGE", "links": None}],
        "properties": {},
        "widgets_values": [prefix]
    })

    # Connect Links table
    links.append([unet_link, 469, 0, 475, 0, "MODEL"])
    links.append([clip_link, 471, 0, 470, 0, "CLIP"])
    if vae_to_textencode_link:
        slot_idx = len(text_inputs) - 1
        links.append([vae_to_textencode_link, 472, 0, 470, slot_idx, "VAE"])
    links.append([vae_to_decode_link, 472, 0, 474, 1, "VAE"])
    links.append([latent_link, 473, 0, 475, 3, "LATENT"])
    links.append([pos_link, 470, 0, 475, 1, "CONDITIONING"])
    links.append([neg_link, 470, 1, 475, 2, "CONDITIONING"])
    links.append([sample_latent_link, 475, 0, 474, 0, "LATENT"])
    links.append([decode_img_link, 474, 0, 494, 0, "IMAGE"])

    for slot_num, lk, nid in image_links:
        links.append([lk, nid, 0, 470, slot_num, "IMAGE"])

    # UI Groups for visual clarity
    groups = [
        {
            "id": 1,
            "title": "1. 核心模型加载 (UNet / CLIP / VAE)",
            "bounding": [70, 40, 360, 440],
            "color": "#3f51b5",
            "font_size": 24
        },
        {
            "id": 2,
            "title": f"2. 安全网格定义 (Issue #16435 防崩锁死: {width}x{height})",
            "bounding": [70, 490, 360, 160],
            "color": "#e91e63",
            "font_size": 24
        },
        {
            "id": 3,
            "title": f"3. Qwen 提示词与条件编码 (Safe Res: {resolution})",
            "bounding": [450, 40, 510, 560],
            "color": "#4caf50",
            "font_size": 24
        },
        {
            "id": 4,
            "title": "4. 采样与图像解码输出 (RX 7900 XTX / CUDA)",
            "bounding": [970, 40, 900, 350],
            "color": "#ff9800",
            "font_size": 24
        }
    ]
    if images:
        groups.append({
            "id": 5,
            "title": "5. 参考图输入源 (物料/底图 Canvas)",
            "bounding": [70, 650, max(360, len(images) * 340 + 40), 380],
            "color": "#009688",
            "font_size": 24
        })

    return {
        "id": str(uuid.uuid4()),
        "revision": 0,
        "last_node_id": 4800 + len(images) + 100,
        "last_link_id": link_id_counter,
        "nodes": nodes,
        "links": links,
        "groups": groups,
        "config": {},
        "extra": {
            "title": title,
            "ds": {"scale": 0.75, "offset": [150, 120]},
            "frontendVersion": "1.47.12"
        },
        "version": 0.4
    }

# ==============================================================================
# 3. Define 8 Concrete Templates
# ==============================================================================

TEMPLATES = [
    {
        "name": "01_safe_edit_text",
        "title": "01_QwenImage_Safe_Edit_Text_Guidance",
        "desc": "单图空心红圈纯文本局部换装与编辑（防过锐与黑斑锁死网格）",
        "type": "edit",
        "width": 928,
        "height": 1216,
        "res": 1056,
        "steps": 32,
        "images": ["m1_base_beauty_hollow_red_2k.png"],
        "prompt": "Use <image1> as the canvas for the person, pose, composition, and background, and edit only the clothing area enclosed by the red outline. Replace the casual sweater with a tailored charcoal-grey Italian wool blazer, fitted white silk shirt underneath, delicate fabric texture, and realistic textile folds. Remove the red outline from the final result. Preserve the subject's face, skin, hair, and clean modern studio background from <image1> exactly unchanged.",
        "prefix": "safe_edit_text"
    },
    {
        "name": "02_safe_edit_ref",
        "title": "02_QwenImage_Safe_Edit_Reference_Transfer",
        "desc": "双图物料参考精准换装（<image1>画布 + <image2>物料参考）",
        "type": "edit",
        "width": 928,
        "height": 1216,
        "res": 1056,
        "steps": 35,
        "images": ["m1_base_beauty_hollow_red_2k.png", "m2_couture_dress_ref.png"],
        "prompt": "Use <image1> as the canvas for the person, pose, composition, and background, and edit only the clothing area enclosed by the red outline. Use <image2> as the reference for the garment design, colors, delicate embroidery patterns, and fabric materials, completely replacing the original clothing with the luxury haute couture tweed dress from <image2>. Accurately adapt the dress to the standing pose, including natural folds and realistic shadows. Completely remove the red outline. Preserve the model's identity, facial features, crystal-clear cold white skin tone, hairstyle, and modern studio background from <image1> exactly unchanged.",
        "prefix": "safe_edit_ref"
    },
    {
        "name": "03_safe_t2i_portrait_2k",
        "title": "03_QwenImage_Safe_T2I_2K_Portrait",
        "desc": "原生 2K 竖版写实肖像（凝脂微距 SSS 肤质与自然发丝）",
        "type": "t2i",
        "width": 1376,
        "height": 1824,
        "res": 1824,
        "steps": 32,
        "images": [],
        "prompt": "Extreme cinematic close-up portrait of a breathtakingly gorgeous East Asian woman in her mid-20s, looking directly at the camera with gentle and serene eyes. Natural skin texture with visible fine pores, soft sub-surface scattering (SSS), delicate peach fuzz along the cheekbones, no excessive makeup, translucent pale skin. Subtle warm rim lighting defining her silhouette against a minimalist concrete and timber architectural background. 85mm portrait lens, f/1.8 aperture, soft cinematic bokeh, 8k resolution, photorealistic masterpiece, Hasselblad H6D-100c quality.",
        "prefix": "safe_t2i_portrait_2k"
    },
    {
        "name": "04_safe_t2i_landscape_2k",
        "title": "04_QwenImage_Safe_T2I_2K_Landscape",
        "desc": "原生 2K 横版大景与严苛排版（杂志双语排版/极简构图）",
        "type": "t2i",
        "width": 1824,
        "height": 1216,
        "res": 1824,
        "steps": 32,
        "images": [],
        "prompt": "High-end fashion editorial magazine spread, wide landscape 16:9 ratio. Elegant and clean typography design. On the top center, the bold elegant serif English letters 'VOGUE ORIENT' are impeccably printed. Below it, in refined traditional Chinese Songti font: '东方留白 美学新生'. In the center of the frame stands a slender model in an avant-garde monochrome silk ensemble amidst misty bamboo waters. Ultra-clean typography, zero typos, perfectly straight letter edges, luxury print design layout.",
        "prefix": "safe_t2i_landscape_2k"
    },
    {
        "name": "05_safe_character_pose",
        "title": "05_QwenImage_Safe_Character_Pose_Recreation",
        "desc": "三视图/设定集驱动的复杂动态姿势重绘（保身份一贯性）",
        "type": "edit",
        "width": 1824,
        "height": 1216,
        "res": 1056,
        "steps": 35,
        "images": ["m4_character_sheet_ref.png"],
        "prompt": "Use <image1> as the character identity and clothing reference. Generate a full-body dynamic cinematic wide shot of the same character slowly walking along a wooden pavilion terrace by a lotus pond at twilight. She gently turns her head back towards the camera with an enigmatic gaze. Maintain 100% facial features, hairstyle, hair accessories, and the exact intricate hanfu embroidery patterns from <image1>. Atmospheric lanterns cast warm amber reflections across ripples in the water, cinematic lighting, masterpiece.",
        "prefix": "safe_char_pose"
    },
    {
        "name": "06_safe_commercial_ad",
        "title": "06_QwenImage_Safe_Commercial_Product_Ad",
        "desc": "商业产品/香水人货焦散与握持交互（手部解剖与光学折射）",
        "type": "edit",
        "width": 928,
        "height": 1216,
        "res": 1056,
        "steps": 32,
        "images": ["m1_base_beauty_2k.png", "m3_perfume_bottle_ref.png"],
        "prompt": "Use <image1> as the canvas for the model, pose, and background. Seamlessly composite the luxury perfume bottle from <image2> into her right hand. The fingers gracefully wrap around the faceted crystal flacon with anatomical precision. Realistic amber liquid refraction, specular highlights, and golden caustic patterns project onto her hand and dress. Studio rim lighting, luxury advertising photography, 8k resolution, crisp commercial grade quality.",
        "prefix": "safe_commercial_ad"
    },
    {
        "name": "07_safe_rgba_transparent",
        "title": "07_QwenImage_Safe_RGBA_Transparent_Asset",
        "desc": "原生 4 通道 RGBA 资产直出（免扣绿幕/半透玻璃烟雾）",
        "type": "t2i",
        "width": 1536,
        "height": 1536,
        "res": 1536,
        "steps": 35,
        "images": [],
        "prompt": "RGBA, isolated on transparent background, alpha channel. A masterfully handcrafted blown glass crane with translucent wings, delicate feather grooves, and internal swirling gold foil dust. Wisps of semi-transparent cyan smoke curl gracefully upwards from its base. Completely transparent alpha background, clean edges, zero solid background color, photorealistic glass dispersion, 8k resolution 3D game asset render.",
        "prefix": "safe_rgba_crane"
    },
    {
        "name": "08_safe_multiref_group",
        "title": "08_QwenImage_Safe_MultiRef_Group_Portrait",
        "desc": "多肖像库并发群像合照（10 位异域人物多参考图对齐）",
        "type": "edit",
        "width": 1216,
        "height": 928,
        "res": 1056,
        "steps": 35,
        "images": [f"m5_avatar_{i:02d}.png" for i in range(1, 11)],
        "prompt": "A panoramic cinematic group portrait of 10 distinct women standing together on a sunlit Santorini terrace overlooking the Aegean Sea. Each woman's facial identity, ethnicity, skin tone, eye shape, and hairstyle corresponds faithfully and uniquely to <image1> through <image10> respectively. Perfect natural smiles, individual postures, golden hour Mediterranean sun casting soft shadows, crisp sharp focus across all faces, zero face blending or mutation.",
        "prefix": "safe_multiref_group"
    }
]

def main():
    print("[*] Generating Qwen-Image-2.1 Safe Latent Grid Templates...")
    
    for tpl in TEMPLATES:
        name = tpl["name"]
        
        # 1. API JSON
        if tpl["type"] == "t2i":
            api_data = make_api_t2i(
                width=tpl["width"],
                height=tpl["height"],
                steps=tpl["steps"],
                prompt=tpl["prompt"],
                prefix=tpl["prefix"]
            )
        else:
            api_data = make_api_edit(
                image_names=tpl["images"],
                width=tpl["width"],
                height=tpl["height"],
                resolution=tpl["res"],
                steps=tpl["steps"],
                prompt=tpl["prompt"],
                prefix=tpl["prefix"]
            )
            
        api_path = API_DIR / f"{name}.json"
        with open(api_path, "w", encoding="utf-8") as f:
            json.dump(api_data, f, indent=2, ensure_ascii=False)
        print(f" [✓] Created API template: {api_path.name}")

        # 2. Web UI JSON
        web_data = make_web_workflow(
            title=tpl["title"],
            prompt=tpl["prompt"],
            width=tpl["width"],
            height=tpl["height"],
            resolution=tpl["res"],
            images=tpl["images"],
            steps=tpl["steps"],
            prefix=tpl["prefix"]
        )
        web_path = WEB_DIR / f"{name}_web.json"
        with open(web_path, "w", encoding="utf-8") as f:
            json.dump(web_data, f, indent=2, ensure_ascii=False)
        print(f" [✓] Created Web UI template: {web_path.name}")

    print(f"\n[✓] All {len(TEMPLATES)} templates successfully created in:")
    print(f"    - API: {API_DIR}")
    print(f"    - Web UI: {WEB_DIR}")

if __name__ == "__main__":
    main()
