import ffmpeg
import os
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip

def get_output_path(input_path, suffix):
    """Generates a unique output path."""
    if not os.path.exists("outputs"):
        os.makedirs("outputs")
    base, ext = os.path.splitext(os.path.basename(input_path))
    output_filename = f"{base}_{suffix}{ext}"
    return os.path.join("outputs", output_filename)

def trim_video(video_path: str, start_time: int, end_time: int) -> str:
    """
    Trims a video from a start time to an end time.
    """
    try:
        output_path = get_output_path(video_path, f"trimmed_{start_time}_{end_time}")
        (
            ffmpeg
            .input(video_path, ss=start_time)
            .to(output_path, t=end_time - start_time)
            .run(overwrite_output=True, quiet=True)
        )
        return f"Video successfully trimmed. New video saved at: {output_path}"
    except Exception as e:
        return f"Error trimming video: {e}"

def change_speed(video_path: str, speed_factor: float) -> str:
    """
    Changes the speed of a video by a given factor.
    Factor > 1 for fast-forward, < 1 for slow-motion.
    """
    try:
        output_path = get_output_path(video_path, f"speed_{speed_factor}x")
        (
            ffmpeg
            .input(video_path)
            .filter('setpts', f'{1/speed_factor}*PTS')
            .output(output_path)
            .run(overwrite_output=True, quiet=True)
        )
        return f"Video speed changed. New video saved at: {output_path}"
    except Exception as e:
        return f"Error changing video speed: {e}"

def add_text_overlay(video_path: str, text: str, fontsize: int = 24, color: str = 'white', position: tuple = ('center', 'center')) -> str:
    """
    Adds a text overlay to a video using MoviePy.
    """
    try:
        output_path = get_output_path(video_path, "text_overlay")
        video_clip = VideoFileClip(video_path)
        text_clip = TextClip(text, fontsize=fontsize, color=color, font='Arial').set_position(position).set_duration(video_clip.duration)
        final_clip = CompositeVideoClip([video_clip, text_clip])
        final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac', temp_audiofile='temp-audio.m4a', remove_temp=True)
        video_clip.close()
        return f"Text overlay added. New video saved at: {output_path}"
    except Exception as e:
        return f"Error adding text overlay: {e}"

def crop_video(video_path: str, x1: int, y1: int, x2: int, y2: int) -> str:
    """
    Crops a video to a given rectangle (x1, y1, x2, y2).
    """
    try:
        output_path = get_output_path(video_path, f"cropped_{x1}_{y1}_{x2}_{y2}")
        width = x2 - x1
        height = y2 - y1
        (
            ffmpeg
            .input(video_path)
            .crop(x1, y1, width, height)
            .output(output_path)
            .run(overwrite_output=True, quiet=True)
        )
        return f"Video successfully cropped. New video saved at: {output_path}"
    except Exception as e:
        return f"Error cropping video: {e}"

