#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
生成简单的示例音效文件
这个脚本会生成一个简单的提醒音效文件（如果pygame可用）
"""

import os
import sys

try:
    import pygame
    import numpy as np
    SOUND_AVAILABLE = True
except ImportError:
    SOUND_AVAILABLE = False
    print("警告：pygame或numpy未安装，无法生成音效文件")

def create_beep_sound(filename, duration=0.5, frequency=800, sample_rate=22050):
    """创建一个简单的提示音"""
    if not SOUND_AVAILABLE:
        return False
        
    try:
        # 初始化pygame mixer
        pygame.mixer.pre_init(sample_rate, -16, 2, 512)
        pygame.mixer.init()
        
        # 生成正弦波音频数据
        frames = int(duration * sample_rate)
        arr = np.zeros((frames, 2))
        
        for i in range(frames):
            time = float(i) / sample_rate
            # 添加淡入淡出效果
            fade_frames = int(0.1 * sample_rate)  # 0.1秒淡入淡出
            if i < fade_frames:
                volume = i / fade_frames
            elif i > frames - fade_frames:
                volume = (frames - i) / fade_frames
            else:
                volume = 1.0
                
            wave = volume * np.sin(2 * np.pi * frequency * time)
            arr[i] = [wave, wave]
        
        # 转换为pygame可用的格式
        arr = (arr * 32767).astype(np.int16)
        sound = pygame.sndarray.make_sound(arr)
        
        # 保存为WAV文件
        pygame.mixer.quit()
        pygame.mixer.init()
        pygame.mixer.music.load(sound)
        
        # 直接使用numpy保存
        from scipy.io import wavfile
        wavfile.write(filename, sample_rate, arr)
        
        return True
        
    except ImportError:
        print("需要安装numpy和scipy来生成音效文件")
        return False
    except Exception as e:
        print(f"生成音效文件失败: {e}")
        return False

def main():
    """主函数"""
    sounds_dir = os.path.join(os.path.dirname(__file__), "sounds")
    
    if not os.path.exists(sounds_dir):
        os.makedirs(sounds_dir)
    
    # 创建不同的提示音
    sounds_to_create = [
        ("notification.wav", 0.5, 800),  # 标准提示音
        ("gentle.wav", 0.8, 600),        # 轻柔提示音
        ("urgent.wav", 0.3, 1000),       # 紧急提示音
    ]
    
    success_count = 0
    for filename, duration, frequency in sounds_to_create:
        filepath = os.path.join(sounds_dir, filename)
        if create_beep_sound(filepath, duration, frequency):
            print(f"✓ 成功创建音效文件: {filename}")
            success_count += 1
        else:
            print(f"✗ 创建音效文件失败: {filename}")
    
    if success_count > 0:
        print(f"\n总共创建了 {success_count} 个音效文件在 {sounds_dir} 目录中")
    else:
        print("\n未能创建任何音效文件，请检查依赖安装情况")
        print("提示：可以手动将您喜欢的音效文件（.wav, .mp3等）放到 sounds 目录中")

if __name__ == "__main__":
    main()
