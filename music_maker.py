import os
from pynput import keyboard
import sys
from moviepy.editor import VideoFileClip, concatenate_videoclips  # 更正导入路径
from getpass import getpass  # 新增导入
from tkinter import Tk, filedialog  # 新增导入

key_sequence = []
negative_flag = False

def on_press(key):
    global negative_flag
    try:
        if key.char == '-':
            negative_flag = True
        elif key.char.isdigit():
            number = int(key.char)
            if negative_flag:
                number = -number
                negative_flag = False
            key_sequence.append(number)
            print(f"输入: {number}")  # 打印当前输入
    except AttributeError:
        # 检查小键盘数字键
        if hasattr(key, 'vk') and 96 <= key.vk <= 105:  # 小键盘数字键的虚拟键码范围是 96-105
            number = key.vk - 96
            if negative_flag:
                number = -number
                negative_flag = False
            key_sequence.append(number)
            print(f"输入: {number}")  # 打印当前输入
        elif key == keyboard.Key.backspace:  # 检查删除键
            if key_sequence:
                removed = key_sequence.pop()
                print(f"删除: {removed}")  # 打印删除的输入
        elif key == keyboard.Key.enter:
            # 清空缓冲区
            negative_flag = False
            return False  # 结束监听
    return True

import re

def load_sequence_from_file(file_path):
    """从文本文件加载数字顺序，支持逗号、空格、换行混合分隔，自动忽略非法内容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

            # 使用正则提取所有合法的整数（支持负号）
            number_strs = re.findall(r'-?\d+', content)
            sequence = [int(num) for num in number_strs]

            print(f"✅ 从文件加载顺序成功：{sequence}")
            return sequence
    except FileNotFoundError:
        print(f"❌ 文件未找到：{file_path}")
    except Exception as e:
        print(f"❌ 无法从文件加载顺序：{e}")
    return []


def select_file_via_dialog(starting_path="."):
    """通过文件选择对话框选择文件"""
    try:
        root = Tk()
        root.withdraw()  # 隐藏主窗口
        root.attributes('-topmost', True)  # 窗口置顶
        file_path = filedialog.askopenfilename(
            initialdir=starting_path, 
            title="选择文本文件", 
            filetypes=[("文本文件", "*.txt")]
        )
        root.destroy()
        return file_path
    except Exception as e:
        print(f"❌ 文件选择出错：{e}")
        return None

def batch_concatenate_videos(video_clips, batch_size=5):
    """分批合成视频"""
    batches = [video_clips[i:i + batch_size] for i in range(0, len(video_clips), batch_size)]
    temp_clips = []
    temp_paths = []  # 用于存储临时文件路径

    for idx, batch in enumerate(batches):
        print(f"正在合成第 {idx + 1} 批视频...")
        try:
            temp_clip = concatenate_videoclips(batch)
            temp_path = f"temp_batch_{idx + 1}.mp4"
            temp_clip.write_videofile(temp_path, codec="libx264")
            temp_clips.append(VideoFileClip(temp_path))
            temp_paths.append(temp_path)
        finally:
            for clip in batch:
                clip.close()

    return temp_clips, temp_paths

def main():
    print("请选择输入方式：")
    print("1. 手动输入")
    print("2. 从文本文件加载顺序")
    try:
        input_choice = int(input("请输入选项编号（1 或 2）："))
        if input_choice == 1:
            print("请输入数字（支持负号），按 Enter 结束：")
            # 开始监听键盘
            with keyboard.Listener(on_press=on_press) as listener:
                listener.join()
            getpass("\n")
        elif input_choice == 2:
            print("请通过文件选择对话框选择文本文件...")
            file_path = select_file_via_dialog()
            if file_path and os.path.exists(file_path):
                global key_sequence
                key_sequence = load_sequence_from_file(file_path)
            else:
                print("❌ 文件不存在或未选择文件，退出。")
                return
        else:
            print("❌ 无效的选项，退出。")
            return
    except ValueError:
        print("❌ 输入无效，退出。")
        return

    print(f"\n录入顺序：{key_sequence}\n")

    video_clips = []
    material_path = "./material"
    if not os.path.exists(material_path):
        print("❌ 未找到 material 文件夹，退出。")
        return

    # 获取 material 文件夹中的所有子文件夹
    subfolders = [f for f in os.listdir(material_path) if os.path.isdir(os.path.join(material_path, f))]
    if not subfolders:
        print("❌ material 文件夹中没有任何素材，退出。")
        return

    print("可用素材列表：")
    for idx, folder in enumerate(subfolders, start=1):
        print(f"{idx}. {folder}")

    # 让用户选择素材文件夹
    try:
        choice = int(input("请选择素材文件夹编号：")) - 1
        if choice < 0 or choice >= len(subfolders):
            print("❌ 无效的选择，退出。")
            return
        selected_folder = subfolders[choice]
    except ValueError:
        print("❌ 输入无效，退出。")
        return

    selected_path = os.path.join(material_path, selected_folder)
    print(f"已选择素材文件夹：{selected_folder}")

    for num in key_sequence:
        video_path = os.path.join(selected_path, f"{num}.mp4")
        if os.path.exists(video_path):
            try:
                clip = VideoFileClip(video_path)
                video_clips.append(clip)
            except Exception as e:
                print(f"⚠️ 加载视频 {video_path} 出错：{e}")
        else:
            # 如果没有找到对应视频，尝试使用相反数的名称
            alt_video_path = os.path.join(selected_path, f"{-num}.mp4")
            if os.path.exists(alt_video_path):
                try:
                    clip = VideoFileClip(alt_video_path)
                    video_clips.append(clip)
                except Exception as e:
                    print(f"⚠️ 加载视频 {alt_video_path} 出错：{e}")
            else:
                print(f"⚠️ 未找到文件：{video_path} 或 {alt_video_path}")

    if video_clips:
        try:
            # 分批合成视频
            temp_clips, temp_paths = batch_concatenate_videos(video_clips, batch_size=10)
            print("正在合成最终视频...")
            final_clip = concatenate_videoclips(temp_clips)
            output_path = "output.mp4"
            final_clip.write_videofile(output_path, codec="libx264")
            print(f"✅ 合成成功，保存到：{output_path}")
        finally:
            for clip in temp_clips:
                clip.close()
            # 删除临时文件
            for temp_path in temp_paths:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    print(f"🗑️ 已删除临时文件：{temp_path}")
    else:
        print("❌ 未能找到任何有效的视频，退出。")

if __name__ == "__main__":
    main()
