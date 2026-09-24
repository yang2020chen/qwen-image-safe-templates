#!/usr/bin/env python3
"""
pipeline.py - Turn-key CLI & SDK for Qwen-Image-2.1 Safe Latent Grid Workflows
Solves ComfyUI Issue #16435 (RoPE Latent Frequency Resonance & Deep-fried Artifacts)

Universal ComfyUI REST API client:
- 100% pure HTTP communication (POST /upload/image, /prompt, /history, /view)
- Zero SSH/SCP dependency, cross-platform (macOS / Linux / Windows)
- Zero sensitive data: config via CLI flag --server or environment variable COMFY_URL
"""

import argparse
import json
import math
import os
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from PIL import Image
import requests

# Add current script directory to sys.path for local module imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

DEFAULT_SERVER_URL = os.environ.get("COMFY_URL", "http://127.0.0.1:8188")

UNET_MODEL = "qwen_image_2.1_int8_convrot.safetensors"
CLIP_MODEL = "qwen3vl_8b_w4a8.safetensors"
VAE_MODEL = "qwen_image_2.1_vae_bf16.safetensors"

SAFE_RESOLUTION = 1056

def calculate_safe_grid(width: int, height: int, resolution: int = SAFE_RESOLUTION) -> Tuple[int, int]:
    """
    Calculate safe EmptyLatent canvas dimensions matching Qwen-Image-2.1 Lanczos resizing rule:
    w = round(sqrt(res^2 * ratio) / 32) * 32
    h = round(sqrt(res^2 / ratio) / 32) * 32
    """
    if width <= 0 or height <= 0:
        return 928, 1216
    ratio = width / height
    safe_w = int(round(math.sqrt(resolution * resolution * ratio) / 32) * 32)
    safe_h = int(round(math.sqrt(resolution * resolution / ratio) / 32) * 32)
    return safe_w, safe_h

class QwenSafeStudio:
    def __init__(self, server_url: Optional[str] = None):
        self.server_url = (server_url or DEFAULT_SERVER_URL).rstrip("/")

    def upload_image(self, local_path: Union[str, Path], remote_filename: Optional[str] = None) -> str:
        """
        Upload local image to ComfyUI input directory via standard REST API POST /upload/image.
        Works across all local and remote ComfyUI installations without SSH.
        """
        local_path = Path(local_path)
        if not local_path.exists():
            raise FileNotFoundError(f"Local file does not exist: {local_path}")
        remote_filename = remote_filename or local_path.name
        
        url = f"{self.server_url}/upload/image"
        with open(local_path, "rb") as f:
            files = {"image": (remote_filename, f, "image/png")}
            data = {"overwrite": "true"}
            resp = requests.post(url, files=files, data=data, timeout=60)
            if resp.status_code != 200:
                raise RuntimeError(f"Failed to upload image to ComfyUI ({url}): HTTP {resp.status_code} - {resp.text}")
            res = resp.json()
            return res.get("name", remote_filename)

    def submit_prompt(self, workflow_dict: dict) -> str:
        data = json.dumps({"prompt": workflow_dict}).encode("utf-8")
        req = urllib.request.Request(f"{self.server_url}/prompt", data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            res = json.loads(resp.read().decode())
            return res["prompt_id"]

    def wait_and_download(self, prompt_id: str, dest_path: Union[str, Path], max_wait: int = 300) -> Path:
        dest_path = Path(dest_path)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        t0 = time.time()
        print(f"[*] Waiting for execution of {prompt_id} on {self.server_url}...")

        while time.time() - t0 < max_wait:
            try:
                with urllib.request.urlopen(f"{self.server_url}/history/{prompt_id}", timeout=5) as resp:
                    hist = json.loads(resp.read().decode())
                    if prompt_id in hist:
                        status = hist[prompt_id].get("status", {})
                        if status.get("completed", False):
                            outputs = hist[prompt_id].get("outputs", {})
                            for nid, out in outputs.items():
                                if "images" in out and len(out["images"]) > 0:
                                    img_info = out["images"][0]
                                    fn = img_info["filename"]
                                    subfolder = img_info.get("subfolder", "")
                                    img_type = img_info.get("type", "output")
                                    
                                    q = urllib.parse.urlencode({"filename": fn, "subfolder": subfolder, "type": img_type})
                                    img_url = f"{self.server_url}/view?{q}"
                                    with urllib.request.urlopen(img_url, timeout=30) as img_resp:
                                        dest_path.write_bytes(img_resp.read())
                                    
                                    elapsed = time.time() - t0
                                    print(f"[✓] Generation complete in {elapsed:.1f}s -> {dest_path}")
                                    return dest_path
            except Exception:
                pass
            time.sleep(3)
        raise TimeoutError(f"Generation timed out after {max_wait}s on {self.server_url}")

    def run_t2i(self, prompt: str, width: int = 928, height: int = 1216, steps: int = 32, seed: int = 202609, output: Union[str, Path] = "output_t2i.png") -> Path:
        """
        Execute safe text-to-image generation.
        """
        graph = {
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
                    "resolution": max(width, height) if max(width, height) <= 1824 else 1056
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
            "494": {"class_type": "SaveImage", "inputs": {"images": ["474", 0], "filename_prefix": "qwen_safe_t2i"}}
        }
        pid = self.submit_prompt(graph)
        return self.wait_and_download(pid, output)

    def run_edit(self, image_path: Union[str, Path], prompt: str, steps: int = 32, seed: int = 202609, output: Union[str, Path] = "output_edit.png") -> Path:
        """
        Execute safe inpainting / local edit on a red-outline canvas image.
        Automatically calculates 1056 Safe Latent Grid to prevent Issue #16435.
        """
        image_path = Path(image_path)
        with Image.open(image_path) as im:
            orig_w, orig_h = im.size
        
        safe_w, safe_h = calculate_safe_grid(orig_w, orig_h, resolution=SAFE_RESOLUTION)
        print(f"[*] Input resolution: {orig_w}x{orig_h} -> 1056 Safe Latent Grid: {safe_w}x{safe_h}")
        
        remote_fn = f"edit_canvas_{int(time.time())}_{image_path.name}"
        self.upload_image(image_path, remote_fn)

        graph = {
            "469": {"class_type": "UNETLoader", "inputs": {"unet_name": UNET_MODEL, "weight_dtype": "default"}},
            "471": {"class_type": "CLIPLoader", "inputs": {"clip_name": CLIP_MODEL, "type": "qwen_image", "device": "default"}},
            "472": {"class_type": "VAELoader", "inputs": {"vae_name": VAE_MODEL}},
            "473": {"class_type": "EmptyLatentImage", "inputs": {"width": safe_w, "height": safe_h, "batch_size": 1}},
            "4801": {"class_type": "LoadImage", "inputs": {"image": remote_fn}},
            "470": {
                "class_type": "TextEncodeQwenImage21",
                "inputs": {
                    "clip": ["471", 0],
                    "vae": ["472", 0],
                    "images.image_1": ["4801", 0],
                    "resolution": SAFE_RESOLUTION,
                    "prompt": prompt,
                    "negative_prompt": ""
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
            "494": {"class_type": "SaveImage", "inputs": {"images": ["474", 0], "filename_prefix": "qwen_safe_edit"}}
        }
        pid = self.submit_prompt(graph)
        return self.wait_and_download(pid, output)

def main():
    parser = argparse.ArgumentParser(description="Qwen-Image-2.1 Safe Latent Studio Pipeline")
    parser.add_argument("--server", type=str, default=DEFAULT_SERVER_URL, help=f"ComfyUI server URL (default: {DEFAULT_SERVER_URL} or COMFY_URL env)")
    subparsers = parser.add_subparsers(dest="command")

    # Command: calc-grid
    p_grid = subparsers.add_parser("calc-grid", help="Calculate 1056 Safe Latent Grid dimensions")
    p_grid.add_argument("--width", type=int, required=True, help="Original image width")
    p_grid.add_argument("--height", type=int, required=True, help="Original image height")
    p_grid.add_argument("--resolution", type=int, default=1056, help="Target TextEncode resolution (default: 1056)")

    # Command: t2i
    p_t2i = subparsers.add_parser("t2i", help="Run safe Text-to-Image generation")
    p_t2i.add_argument("--prompt", type=str, required=True, help="Text prompt")
    p_t2i.add_argument("--width", type=int, default=928, help="Latent width (default: 928)")
    p_t2i.add_argument("--height", type=int, default=1216, help="Latent height (default: 1216)")
    p_t2i.add_argument("--steps", type=int, default=32, help="Sampling steps (default: 32)")
    p_t2i.add_argument("--seed", type=int, default=202609, help="Random seed (default: 202609)")
    p_t2i.add_argument("--output", type=str, default="output_t2i.png", help="Output path (default: output_t2i.png)")

    # Command: edit
    p_edit = subparsers.add_parser("edit", help="Run safe inpainting / local edit on red-outline canvas")
    p_edit.add_argument("--image", type=str, required=True, help="Canvas image path with hollow red outline")
    p_edit.add_argument("--prompt", type=str, required=True, help="Text prompt with <image1> instructions")
    p_edit.add_argument("--steps", type=int, default=32, help="Sampling steps (default: 32)")
    p_edit.add_argument("--seed", type=int, default=202609, help="Random seed (default: 202609)")
    p_edit.add_argument("--output", type=str, default="output_edit.png", help="Output path (default: output_edit.png)")

    # Command: edit-top
    p_top = subparsers.add_parser("edit-top", help="One-step auto-mark top outline and execute safe edit")
    p_top.add_argument("--image", type=str, required=True, help="Base protagonist portrait image")
    p_top.add_argument("--prompt", type=str, required=True, help="Text prompt for top replacement")
    p_top.add_argument("--steps", type=int, default=32, help="Sampling steps (default: 32)")
    p_top.add_argument("--seed", type=int, default=202609, help="Random seed (default: 202609)")
    p_top.add_argument("--output", type=str, default="output_edit_top.png", help="Output path (default: output_edit_top.png)")

    args = parser.parse_args()

    if args.command == "calc-grid":
        w, h = calculate_safe_grid(args.width, args.height, args.resolution)
        print(f"Original: {args.width}x{args.height} -> {args.resolution} Safe Grid: {w}x{h}")
    elif args.command == "t2i":
        studio = QwenSafeStudio(server_url=args.server)
        out = studio.run_t2i(args.prompt, args.width, args.height, args.steps, args.seed, args.output)
        print(f"Result saved to {out}")
    elif args.command == "edit":
        studio = QwenSafeStudio(server_url=args.server)
        out = studio.run_edit(args.image, args.prompt, args.steps, args.seed, args.output)
        print(f"Result saved to {out}")
    elif args.command == "edit-top":
        from mark_outline import mark_top_outline
        temp_dir = Path(tempfile.gettempdir())
        temp_marked = temp_dir / f"auto_marked_top_{int(time.time())}.png"
        mark_top_outline(Path(args.image), temp_marked)
        print(f"[✓] Auto-marked top outline -> {temp_marked}")
        studio = QwenSafeStudio(server_url=args.server)
        out = studio.run_edit(temp_marked, args.prompt, args.steps, args.seed, args.output)
        print(f"Result saved to {out}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
