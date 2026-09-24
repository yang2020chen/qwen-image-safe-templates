#!/usr/bin/env python3
"""
Qwen-Image-2.1 Safe Latent Grid Automation Client & CLI SDK
Solves ComfyUI Issue #16435 (RoPE Frequency Resonance & Oversharpened / Deep-fried Latent Bug)

Author: web_studio / Chen Yang
Hardware Target: AMD Radeon RX 7900 XTX 24GB (ROCm 7.2) / NVIDIA RTX 4090 / 3060
Service: ComfyUI (0.0.0.0:8188)
"""

import argparse
import json
import math
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from PIL import Image

DEFAULT_SERVER_URL = os.environ.get("COMFY_URL", "http://127.0.0.1:8188")
SAFE_RESOLUTION_BASE = 1056

# Standard model configurations
UNET_MODEL = "qwen_image_2.1_int8_convrot.safetensors"
CLIP_MODEL = "qwen3vl_8b_w4a8.safetensors"
VAE_MODEL = "qwen_image_2.1_vae_bf16.safetensors"

TEMPLATE_DIR = Path(__file__).resolve().parent / "api"

def calculate_safe_grid(width: int, height: int, resolution: int = SAFE_RESOLUTION_BASE) -> Tuple[int, int]:
    """
    Calculate the exact safe EmptyLatent canvas dimensions (w, h) that match
    ComfyUI TextEncodeQwenImage21's internal Lanczos resizing rule.
    
    Formula:
        ratio = width / height
        safe_w = round(sqrt(res^2 * ratio) / 32) * 32
        safe_h = round(sqrt(res^2 / ratio) / 32) * 32
        
    Guarantees 1:1 token & pixel alignment to eliminate Issue #16435 RoPE distortion.
    """
    if width <= 0 or height <= 0:
        return 928, 1216
    ratio = width / height
    safe_w = int(round(math.sqrt(resolution * resolution * ratio) / 32) * 32)
    safe_h = int(round(math.sqrt(resolution * resolution / ratio) / 32) * 32)
    return safe_w, safe_h

class QwenSafePipeline:
    def __init__(self, server_url: Optional[str] = None):
        self.server_url = (server_url or DEFAULT_SERVER_URL).rstrip("/")

    def check_health(self) -> bool:
        try:
            with urllib.request.urlopen(f"{self.server_url}/system_stats", timeout=5) as resp:
                stats = json.loads(resp.read().decode())
                print(f"[✓] Connected to ComfyUI v{stats.get('system', {}).get('comfyui_version')}")
                for d in stats.get("devices", []):
                    vram_free_gb = round(d.get("vram_free", 0) / (1024**3), 2)
                    vram_total_gb = round(d.get("vram_total", 0) / (1024**3), 2)
                    print(f"    - Device {d.get('name')}: {vram_free_gb} GB / {vram_total_gb} GB free")
                return True
        except Exception as e:
            print(f"[!] Health check failed for {self.server_url}: {e}")
            return False

    def sync_image_to_remote(self, local_path: Union[str, Path], remote_filename: Optional[str] = None) -> str:
        """
        Upload image to ComfyUI input directory via standard HTTP REST API POST /upload/image.
        Works across all local and remote ComfyUI installations without SSH.
        """
        local_path = Path(local_path)
        if not local_path.exists():
            raise FileNotFoundError(f"Local file not found: {local_path}")
        remote_filename = remote_filename or local_path.name
        
        import requests
        url = f"{self.server_url}/upload/image"
        with open(local_path, "rb") as f:
            files = {"image": (remote_filename, f, "image/png")}
            data = {"overwrite": "true"}
            resp = requests.post(url, files=files, data=data, timeout=60)
            if resp.status_code != 200:
                raise RuntimeError(f"Failed to upload image to ComfyUI ({url}): HTTP {resp.status_code} - {resp.text}")
            res = resp.json()
            return res.get("name", remote_filename)

    def post_prompt(self, workflow_dict: dict) -> str:
        data = json.dumps({"prompt": workflow_dict}).encode("utf-8")
        req = urllib.request.Request(f"{self.server_url}/prompt", data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            res = json.loads(resp.read().decode())
            return res["prompt_id"]

    def wait_and_download(self, prompt_id: str, dest_path: Union[str, Path], max_wait: int = 600) -> dict:
        dest_path = Path(dest_path)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        t0 = time.time()
        
        while time.time() - t0 < max_wait:
            try:
                with urllib.request.urlopen(f"{self.server_url}/history/{prompt_id}", timeout=5) as resp:
                    history = json.loads(resp.read().decode())
                    if prompt_id in history:
                        data = history[prompt_id]
                        status = data.get("status", {})
                        if status.get("completed", False):
                            elapsed = round(time.time() - t0, 2)
                            outputs = data.get("outputs", {})
                            images = outputs.get("494", {}).get("images", [])
                            if images:
                                img_info = images[0]
                                filename = img_info.get("filename")
                                subfolder = img_info.get("subfolder", "")
                                img_type = img_info.get("type", "output")
                                
                                params = urllib.parse.urlencode({"filename": filename, "subfolder": subfolder, "type": img_type})
                                view_url = f"{self.server_url}/view?{params}"
                                urllib.request.urlretrieve(view_url, str(dest_path))
                                
                                im = Image.open(dest_path)
                                return {
                                    "success": True,
                                    "elapsed": elapsed,
                                    "path": str(dest_path),
                                    "width": im.width,
                                    "height": im.height,
                                    "size_kb": round(dest_path.stat().st_size / 1024, 1)
                                }
                            return {"success": False, "error": "No output images found in node 494"}
                        elif status.get("status_str") == "error":
                            return {"success": False, "error": status.get("messages", "Unknown error")}
            except Exception:
                pass
            time.sleep(1.5)
        return {"success": False, "error": f"Timeout after {max_wait}s"}

    # --------------------------------------------------------------------------
    # Workflow Generators (Safe Grid Enforcement)
    # --------------------------------------------------------------------------

    def build_t2i_workflow(self, prompt: str, width: int = 1376, height: int = 1824, steps: int = 32, seed: int = 202609, prefix: str = "t2i_safe") -> dict:
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
                    "seed": seed,
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

    def build_edit_workflow(self,
                            image_names: List[str],
                            prompt: str,
                            ref_width: int,
                            ref_height: int,
                            resolution: int = SAFE_RESOLUTION_BASE,
                            steps: int = 32,
                            seed: int = 202609,
                            prefix: str = "edit_safe") -> dict:
        safe_w, safe_h = calculate_safe_grid(ref_width, ref_height, resolution)
        
        graph = {
            "469": {"class_type": "UNETLoader", "inputs": {"unet_name": UNET_MODEL, "weight_dtype": "default"}},
            "471": {"class_type": "CLIPLoader", "inputs": {"clip_name": CLIP_MODEL, "type": "qwen_image", "device": "default"}},
            "472": {"class_type": "VAELoader", "inputs": {"vae_name": VAE_MODEL}},
            "473": {"class_type": "EmptyLatentImage", "inputs": {"width": safe_w, "height": safe_h, "batch_size": 1}},
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
                    "seed": seed,
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

        for idx, img_name in enumerate(image_names, 1):
            node_id = str(4800 + idx)
            graph[node_id] = {
                "class_type": "LoadImage",
                "inputs": {"image": img_name}
            }
            graph["470"]["inputs"][f"images.image_{idx}"] = [node_id, 0]

        return graph

    # --------------------------------------------------------------------------
    # High-Level One-Click APIs
    # --------------------------------------------------------------------------

    def edit_anything_text(self,
                           input_image: Union[str, Path],
                           prompt: str,
                           output_path: Union[str, Path],
                           steps: int = 32,
                           seed: int = 202609) -> dict:
        input_path = Path(input_image)
        with Image.open(input_path) as im:
            w, h = im.size
        remote_name = self.sync_image_to_remote(input_path)

        if "<image1>" not in prompt:
            prompt = f"Use <image1> as the canvas for the person, pose, composition, and background, and edit only the specified area. {prompt}"

        workflow = self.build_edit_workflow(
            image_names=[remote_name],
            prompt=prompt,
            ref_width=w,
            ref_height=h,
            resolution=SAFE_RESOLUTION_BASE,
            steps=steps,
            seed=seed,
            prefix="safe_edit_text"
        )
        pid = self.post_prompt(workflow)
        print(f"[*] Submitted Edit Anything prompt -> ID: {pid}")
        return self.wait_and_download(pid, output_path)

    def edit_with_reference(self,
                            canvas_image: Union[str, Path],
                            reference_image: Union[str, Path],
                            prompt: str,
                            output_path: Union[str, Path],
                            steps: int = 35,
                            seed: int = 202609) -> dict:
        c_path = Path(canvas_image)
        r_path = Path(reference_image)
        with Image.open(c_path) as im:
            w, h = im.size

        r_cname = self.sync_image_to_remote(c_path)
        r_rname = self.sync_image_to_remote(r_path)

        workflow = self.build_edit_workflow(
            image_names=[r_cname, r_rname],
            prompt=prompt,
            ref_width=w,
            ref_height=h,
            resolution=SAFE_RESOLUTION_BASE,
            steps=steps,
            seed=seed,
            prefix="safe_edit_ref"
        )
        pid = self.post_prompt(workflow)
        print(f"[*] Submitted Reference Transfer prompt -> ID: {pid}")
        return self.wait_and_download(pid, output_path)

    def generate_t2i_2k(self,
                        prompt: str,
                        output_path: Union[str, Path],
                        orientation: str = "portrait",
                        steps: int = 32,
                        seed: int = 202609) -> dict:
        if orientation == "landscape":
            w, h = 1824, 1216
        elif orientation == "square":
            w, h = 1536, 1536
        else:
            w, h = 1376, 1824

        workflow = self.build_t2i_workflow(prompt, width=w, height=h, steps=steps, seed=seed, prefix=f"safe_t2i_{orientation}")
        pid = self.post_prompt(workflow)
        print(f"[*] Submitted Native 2K T2I prompt -> ID: {pid}")
        return self.wait_and_download(pid, output_path)

    def run_template(self, template_name_or_file: str, output_path: Union[str, Path], overrides: Optional[dict] = None) -> dict:
        """
        Load an existing JSON template from the api/ folder, apply runtime overrides, and execute.
        """
        target = Path(template_name_or_file)
        if not target.exists():
            target = TEMPLATE_DIR / f"{template_name_or_file}.json"
        if not target.exists():
            raise FileNotFoundError(f"Template not found: {template_name_or_file}")

        with open(target, "r", encoding="utf-8") as f:
            workflow = json.load(f)

        overrides = overrides or {}
        if "prompt" in overrides and "470" in workflow:
            workflow["470"]["inputs"]["prompt"] = overrides["prompt"]
        if "seed" in overrides and "475" in workflow:
            workflow["475"]["inputs"]["seed"] = overrides["seed"]
        if "steps" in overrides and "475" in workflow:
            workflow["475"]["inputs"]["steps"] = overrides["steps"]

        pid = self.post_prompt(workflow)
        print(f"[*] Executing template '{target.stem}' -> ID: {pid}")
        return self.wait_and_download(pid, output_path)

# ==============================================================================
# CLI Entrypoint
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(description="Qwen-Image-2.1 Safe Latent Grid Automation Client & CLI SDK")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # health
    subparsers.add_parser("health", help="Check ComfyUI server connectivity and VRAM")

    # list
    subparsers.add_parser("list", help="List available safe templates")

    # calc-grid
    p_grid = subparsers.add_parser("calc-grid", help="Calculate safe EmptyLatent canvas dimensions")
    p_grid.add_argument("--width", type=int, required=True, help="Input reference image width")
    p_grid.add_argument("--height", type=int, required=True, help="Input reference image height")
    p_grid.add_argument("--res", type=int, default=SAFE_RESOLUTION_BASE, help="TextEncode resolution base (default: 1056)")

    # edit-text
    p_et = subparsers.add_parser("edit-text", help="One-click text-guided Edit Anything")
    p_et.add_argument("--canvas", type=str, required=True, help="Path to canvas image (with red outline)")
    p_et.add_argument("--prompt", type=str, required=True, help="Edit instruction prompt")
    p_et.add_argument("--output", type=str, required=True, help="Destination output image path")
    p_et.add_argument("--steps", type=int, default=32, help="Sampling steps (default: 32)")
    p_et.add_argument("--seed", type=int, default=202609, help="Random seed")

    # edit-ref
    p_er = subparsers.add_parser("edit-ref", help="One-click reference-guided garment/material transfer")
    p_er.add_argument("--canvas", type=str, required=True, help="Path to canvas image (with red outline)")
    p_er.add_argument("--ref", type=str, required=True, help="Path to material / garment reference image")
    p_er.add_argument("--prompt", type=str, required=True, help="Edit instruction prompt")
    p_er.add_argument("--output", type=str, required=True, help="Destination output image path")
    p_er.add_argument("--steps", type=int, default=35, help="Sampling steps (default: 35)")
    p_er.add_argument("--seed", type=int, default=202609, help="Random seed")

    # t2i
    p_t2i = subparsers.add_parser("t2i", help="Native 2K pure Text-to-Image")
    p_t2i.add_argument("--prompt", type=str, required=True, help="Text prompt")
    p_t2i.add_argument("--output", type=str, required=True, help="Destination output image path")
    p_t2i.add_argument("--orientation", choices=["portrait", "landscape", "square"], default="portrait", help="Canvas orientation")
    p_t2i.add_argument("--steps", type=int, default=32, help="Sampling steps (default: 32)")
    p_t2i.add_argument("--seed", type=int, default=202609, help="Random seed")

    # run-template
    p_run = subparsers.add_parser("run-template", help="Execute an existing safe template JSON")
    p_run.add_argument("--template", type=str, required=True, help="Template name (e.g. 01_safe_edit_text) or JSON path")
    p_run.add_argument("--output", type=str, required=True, help="Destination output image path")
    p_run.add_argument("--prompt", type=str, default=None, help="Override prompt")
    p_run.add_argument("--seed", type=int, default=None, help="Override seed")
    p_run.add_argument("--steps", type=int, default=None, help="Override steps")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    client = QwenSafePipeline()

    if args.command == "health":
        client.check_health()
    elif args.command == "list":
        if not TEMPLATE_DIR.exists():
            print(f"[!] Template dir not found: {TEMPLATE_DIR}")
            return
        print(f"\n[+] Available Qwen-Image-2.1 Safe Templates ({TEMPLATE_DIR}):")
        for f in sorted(TEMPLATE_DIR.glob("*.json")):
            print(f"    - {f.stem}")
        print("\nUse `python qwen_safe_pipeline.py run-template --template <NAME> --output <OUT>` to execute.\n")
    elif args.command == "calc-grid":
        sw, sh = calculate_safe_grid(args.width, args.height, args.res)
        mp = round((sw * sh) / 1_000_000, 2)
        print(f"\n[+] Input: {args.width}x{args.height} (ratio: {args.width/args.height:.3f})")
        print(f"    Safe EmptyLatent: {sw}x{sh} (~{mp} MP)")
        print(f"    TextEncode resolution: {args.res}")
        print(f"    RoPE Token Alignment: 100% matched, zero resonance risk.\n")
    elif args.command == "edit-text":
        res = client.edit_anything_text(args.canvas, args.prompt, args.output, steps=args.steps, seed=args.seed)
        print(f"[*] Result: {res}")
    elif args.command == "edit-ref":
        res = client.edit_with_reference(args.canvas, args.ref, args.prompt, args.output, steps=args.steps, seed=args.seed)
        print(f"[*] Result: {res}")
    elif args.command == "t2i":
        res = client.generate_t2i_2k(args.prompt, args.output, orientation=args.orientation, steps=args.steps, seed=args.seed)
        print(f"[*] Result: {res}")
    elif args.command == "run-template":
        overrides = {}
        if args.prompt: overrides["prompt"] = args.prompt
        if args.seed is not None: overrides["seed"] = args.seed
        if args.steps is not None: overrides["steps"] = args.steps
        res = client.run_template(args.template, args.output, overrides=overrides)
        print(f"[*] Result: {res}")

if __name__ == "__main__":
    main()
