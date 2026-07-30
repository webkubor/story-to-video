#!/usr/bin/env python3
"""
儿童绘本故事视频合成管线
修复记录：VoxCraft clone 命令无 --output 参数，输出在 out/ 目录
"""
import subprocess, os, json, glob, shutil
from pathlib import Path

PROJECT = Path.home() / "Desktop" / "personal" / "github" / "story-to-video"

def generate_voiceover(scenes: list[dict]) -> list[str]:
    """用 VoxCraft 合成旁白"""
    voice_editor = Path.home() / "Desktop" / "personal" / "github" / "voice-editor"
    os.makedirs("/tmp/storybook-audio", exist_ok=True)
    files = []
    
    for scene in scenes:
        out = f"/tmp/storybook-audio/{scene['id']}.wav"
        if os.path.exists(out) and os.path.getsize(out) > 1000:
            files.append(out)
            continue
        
        # clone 命令输出在 voice-editor/out/ 目录
        subprocess.run(
            f"cd {voice_editor} && .venv/bin/python -m cli.app clone '{scene['voice_key']}' '{scene['narration']}'",
            capture_output=True, text=True, timeout=60, shell=True
        )
        
        # 从 out/ 目录取最新 wav
        latest = sorted(glob.glob(f"{voice_editor}/out/*.wav"), key=os.path.getmtime)
        if latest:
            shutil.copy2(latest[-1], out)
            files.append(out)
    
    return files
