"""
Final video assembly using FFmpeg.
Combines avatar video + B-roll + voiceover + subtitles into final output.
"""
import os
import asyncio
import uuid
from config import settings


async def assemble_video(
    avatar_video_path: str = None,
    broll_paths: list[str] = None,
    audio_path: str = None,
    output_filename: str = None,
    add_subtitles: bool = True,
    subtitle_srt: str = None,
) -> str:
    """
    Assemble final video from components using FFmpeg.

    Strategy:
    - If avatar_video: use as main track, overlay B-roll during visual cues
    - If only B-roll: montage of clips with voiceover audio
    - Add subtitles burned-in

    Returns:
        Path to final assembled video.
    """
    os.makedirs(settings.output_dir, exist_ok=True)

    if not output_filename:
        output_filename = f"final_{uuid.uuid4().hex[:8]}.mp4"

    output_path = os.path.join(settings.output_dir, output_filename)

    if avatar_video_path and audio_path:
        await _assemble_avatar_with_audio(avatar_video_path, audio_path, output_path)
    elif broll_paths and audio_path:
        await _assemble_broll_with_audio(broll_paths, audio_path, output_path)
    elif avatar_video_path:
        await _copy_to_output(avatar_video_path, output_path)
    else:
        raise ValueError("Need at least avatar_video_path or (broll_paths + audio_path)")

    if add_subtitles and subtitle_srt:
        srt_path = output_path.replace(".mp4", ".srt")
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(subtitle_srt)
        subtitled_path = output_path.replace(".mp4", "_sub.mp4")
        await _burn_subtitles(output_path, srt_path, subtitled_path)
        os.replace(subtitled_path, output_path)

    return output_path


async def _assemble_avatar_with_audio(video_path: str, audio_path: str, output_path: str):
    """Replace video audio with custom voiceover."""
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        output_path,
    ]
    await _run_ffmpeg(cmd)


async def _assemble_broll_with_audio(broll_paths: list[str], audio_path: str, output_path: str):
    """Concatenate B-roll clips and add audio."""
    # Create concat list
    concat_file = output_path.replace(".mp4", "_concat.txt")
    with open(concat_file, "w") as f:
        for path in broll_paths:
            f.write(f"file '{os.path.abspath(path)}'\n")

    # Concat clips
    concat_output = output_path.replace(".mp4", "_raw.mp4")
    cmd_concat = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_file,
        "-c", "copy",
        concat_output,
    ]
    await _run_ffmpeg(cmd_concat)

    # Add audio
    cmd_audio = [
        "ffmpeg", "-y",
        "-i", concat_output,
        "-i", audio_path,
        "-c:v", "copy",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        output_path,
    ]
    await _run_ffmpeg(cmd_audio)

    os.remove(concat_file)
    os.remove(concat_output)


async def _burn_subtitles(video_path: str, srt_path: str, output_path: str):
    """Burn subtitles into video (TikTok-style bold white text)."""
    subtitle_filter = (
        f"subtitles={srt_path}:force_style="
        "'FontName=Arial,FontSize=18,Bold=1,PrimaryColour=&HFFFFFF,"
        "OutlineColour=&H000000,Outline=2,Shadow=1,Alignment=2'"
    )
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", subtitle_filter,
        "-c:a", "copy",
        output_path,
    ]
    await _run_ffmpeg(cmd)


async def _copy_to_output(src: str, dst: str):
    cmd = ["ffmpeg", "-y", "-i", src, "-c", "copy", dst]
    await _run_ffmpeg(cmd)


async def _run_ffmpeg(cmd: list[str]):
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"FFmpeg failed:\n{stderr.decode()}")


def transcript_to_srt(segments: list[dict]) -> str:
    """Convert Whisper segments to SRT subtitle format."""
    lines = []
    for i, seg in enumerate(segments, 1):
        start = _sec_to_srt_time(seg["start"])
        end = _sec_to_srt_time(seg["end"])
        lines.append(f"{i}\n{start} --> {end}\n{seg['text'].strip()}\n")
    return "\n".join(lines)


def _sec_to_srt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
