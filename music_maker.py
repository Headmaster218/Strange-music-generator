import os
from pynput import keyboard
import sys
from moviepy.editor import VideoFileClip, CompositeVideoClip, concatenate_videoclips
from getpass import getpass
from tkinter import Tk, filedialog
import re

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
            key_sequence.append([number])
            print(f"输入: {number}")
    except AttributeError:
        if hasattr(key, 'vk') and 96 <= key.vk <= 105:
            number = key.vk - 96
            if negative_flag:
                number = -number
                negative_flag = False
            key_sequence.append([number])
            print(f"输入: {number}")
        elif key == keyboard.Key.backspace:
            if key_sequence:
                removed = key_sequence.pop()
                print(f"删除: {removed}")
        elif key == keyboard.Key.enter:
            negative_flag = False
            return False
    return True

def load_sequence_from_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            content = re.sub(r'[^\d\-\*]+', ' ', content)
            groups = content.strip().split()
            sequence = []
            for group in groups:
                numbers = []
                for n in group.split('*'):
                    if n.strip():
                        numbers.append(int(n.strip()))
                sequence.append(numbers)
            print(f"✅ 从文件加载顺序成功：{sequence}")
            return sequence
    except FileNotFoundError:
        print(f"❌ 文件未找到：{file_path}")
    except Exception as e:
        print(f"❌ 无法从文件加载顺序：{e}")
    return []

def select_file_via_dialog(starting_path="."):
    try:
        root = Tk()
        root.withdraw()
        root.attributes('-topmost', True)
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

def main():
    print("请选择输入方式：")
    print("1. 手动输入")
    print("2. 从文本文件加载顺序")
    output_filename = "output.mp4"
    try:
        input_choice = int(input("请输入选项编号（1 或 2）："))
        if input_choice == 1:
            print("请输入数字（支持负号），按 Enter 结束：")
            with keyboard.Listener(on_press=on_press) as listener:
                listener.join()
            getpass("\n")
        elif input_choice == 2:
            print("请通过文件选择对话框选择文本文件...")
            file_path = select_file_via_dialog()
            if file_path and os.path.exists(file_path):
                global key_sequence
                key_sequence = load_sequence_from_file(file_path)
                output_filename = os.path.splitext(os.path.basename(file_path))[0] + ".mp4"
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

    material_path = "./material"
    if not os.path.exists(material_path):
        print("❌ 未找到 material 文件夹，退出。")
        return

    subfolders = [f for f in os.listdir(material_path) if os.path.isdir(os.path.join(material_path, f))]
    if not subfolders:
        print("❌ material 文件夹中没有任何素材，退出。")
        return

    print("可用素材列表：")
    for idx, folder in enumerate(subfolders, start=1):
        print(f"{idx}. {folder}")

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

    video_cache = {}
    for fname in os.listdir(selected_path):
        if fname.endswith(".mp4"):
            fpath = os.path.join(selected_path, fname)
            try:
                clip = VideoFileClip(fpath)
                video_cache[fname] = clip
            except Exception as e:
                print(f"⚠️ 加载视频 {fname} 出错：{e}")

    video_clips = []
    for group in key_sequence:
        clips = []
        for num in group:
            if num == 0:
                name = "0.mp4"
            else:
                sign = -1 if num < 0 else 1
                mapped_num = sign * ((abs(num) - 1) % 7 + 1)
                name = f"{mapped_num}.mp4"
                alt_name = f"{-mapped_num}.mp4"
            clip = video_cache.get(name)
            if not clip and num != 0:
                clip = video_cache.get(alt_name)
            if clip:
                clips.append(clip)
            else:
                print(f"⚠️ 未找到视频：{name} 或 {alt_name}")
        if clips:
            width = clips[0].w
            positioned = [c.set_position((i * width, 0)) for i, c in enumerate(clips)]
            combined = CompositeVideoClip(positioned).set_duration(clips[0].duration)
            video_clips.append(combined)

    if video_clips:
        try:
            print("正在合成最终视频...")
            final_video = concatenate_videoclips(video_clips)
            output_dir = "./output"
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, output_filename)
            final_video.write_videofile(output_path, codec="libx264")
            print(f"✅ 合成成功，保存到：{output_path}")
        finally:
            for clip in video_clips:
                clip.close()
    else:
        print("❌ 未能找到任何有效的视频，退出。")

if __name__ == "__main__":
    main()
