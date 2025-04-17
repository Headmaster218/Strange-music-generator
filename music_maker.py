import os
from pynput import keyboard
import sys
from moviepy.editor import VideoFileClip, concatenate_videoclips  # 更正导入路径
from getpass import getpass  # 新增导入

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

def main():
    print("请输入数字（支持负号），按 Enter 结束：")

    # 开始监听键盘
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

    print(f"\n录入顺序：{key_sequence}\n")
    getpass("\n")

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
        choice = int(input("请选择素材文件夹编号：")) - 1  # 使用 getpass 替代 input
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
            final_clip = concatenate_videoclips(video_clips)
            output_path = "output.mp4"
            final_clip.write_videofile(output_path, codec="libx264")
            print(f"✅ 合成成功，保存到：{output_path}")
        finally:
            for clip in video_clips:
                clip.close()
    else:
        print("❌ 未能找到任何有效的视频，退出。")

if __name__ == "__main__":
    main()
