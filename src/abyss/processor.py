from __future__ import annotations

import os
import traceback
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import av
from av.audio.stream import AudioStream
from av.video.stream import VideoStream
from PIL import Image, ImageOps, UnidentifiedImageError

from abyss.sanitize import safe_temp_path, safe_unique_output_path


_register_heif_opener: Callable[..., None] | None = None
try:
    from pillow_heif import register_heif_opener
except Exception:  # pragma: no cover
    pass
else:
    _register_heif_opener = register_heif_opener


if _register_heif_opener is not None:
    _register_heif_opener()


IMAGE_EXTS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".tif",
    ".tiff",
    ".webp",
    ".heic",
    ".heif",
    ".avif",
}

VIDEO_EXTS = {
    ".mov",
    ".mp4",
    ".m4v",
    ".avi",
    ".mkv",
    ".webm",
    ".mts",
    ".m2ts",
    ".3gp",
    ".3g2",
}


@dataclass(frozen=True)
class ProcessResult:
    source: Path
    status: str
    message: str
    output: Path | None = None


ProgressCallback = Callable[[str], None]


def iter_media_files(paths: Iterable[Path]) -> Iterable[Path]:
    """Yield files from dropped files and folders recursively."""
    for path in paths:
        if path.is_file():
            yield path
        elif path.is_dir():
            for child in sorted(path.rglob("*")):
                if child.is_file():
                    yield child


def is_image(path: Path) -> bool:
    return path.suffix.lower() in IMAGE_EXTS


def is_video(path: Path) -> bool:
    return path.suffix.lower() in VIDEO_EXTS


def process_paths(
    paths: Iterable[Path],
    progress: ProgressCallback | None = None,
) -> list[ProcessResult]:
    results: list[ProcessResult] = []

    for file_path in iter_media_files(paths):
        if progress:
            progress(f"Inspecting: {file_path}")

        try:
            if is_image(file_path):
                result = convert_image_to_jpeg(file_path)
            elif is_video(file_path):
                result = convert_video_to_mp4(file_path)
            else:
                result = ProcessResult(
                    source=file_path,
                    status="skipped",
                    message="Unsupported extension",
                )
        except Exception as exc:
            result = ProcessResult(
                source=file_path,
                status="error",
                message=f"{exc}\n{traceback.format_exc()}",
            )

        results.append(result)

        if progress:
            progress(f"{result.status.upper()}: {file_path.name} - {result.message}")

    return results


def convert_image_to_jpeg(source: Path) -> ProcessResult:
    """Convert an image to JPEG while stripping metadata."""
    source = source.resolve()

    output = safe_unique_output_path(source.parent, source.stem, ".jpg")
    temp = safe_temp_path(output)

    try:
        with Image.open(source) as image:
            image = ImageOps.exif_transpose(image)

            try:
                image.seek(0)
            except EOFError:
                pass

            if image.mode in {"RGBA", "LA"} or (
                image.mode == "P" and "transparency" in image.info
            ):
                rgba = image.convert("RGBA")
                background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
                background.alpha_composite(rgba)
                image = background.convert("RGB")
            else:
                image = image.convert("RGB")

            image.save(
                temp,
                format="JPEG",
                quality=98,
                subsampling=0,
                optimize=True,
                progressive=True,
            )

        _commit_replacement(source=source, temp=temp, output=output)

        return ProcessResult(
            source=source,
            status="done",
            message="Converted to metadata-free JPEG",
            output=output,
        )

    except UnidentifiedImageError as exc:
        _cleanup_temp(temp)
        return ProcessResult(
            source=source,
            status="error",
            message=f"Could not identify image: {exc}",
        )
    except Exception:
        _cleanup_temp(temp)
        raise


def convert_video_to_mp4(source: Path) -> ProcessResult:
    """Convert or remux a video to MP4 while stripping metadata."""
    source = source.resolve()

    output = safe_unique_output_path(source.parent, source.stem, ".mp4")
    temp = safe_temp_path(output)

    try:
        _remux_video_metadata_free(source, temp)
        _commit_replacement(source=source, temp=temp, output=output)

        return ProcessResult(
            source=source,
            status="done",
            message="Remuxed to metadata-free MP4 without re-encoding",
            output=output,
        )

    except Exception as remux_error:
        _cleanup_temp(temp)
        temp = safe_temp_path(output)

        try:
            _reencode_video_metadata_free(source, temp)
            _commit_replacement(source=source, temp=temp, output=output)

            return ProcessResult(
                source=source,
                status="done",
                message=(
                    "Re-encoded to metadata-free MP4 because direct remux failed. "
                    f"Remux error was: {remux_error}"
                ),
                output=output,
            )

        except Exception as encode_error:
            _cleanup_temp(temp)
            return ProcessResult(
                source=source,
                status="error",
                message=(
                    "Video could not be safely converted with the available PyAV codecs. "
                    "Original was left in place. "
                    f"Remux error: {remux_error}. Encode error: {encode_error}"
                ),
            )


def _remux_video_metadata_free(source: Path, temp: Path) -> None:
    """Remux compatible audio/video streams to MP4 without re-encoding."""
    with av.open(str(source), mode="r") as input_container:
        input_streams = [
            stream for stream in input_container.streams if stream.type in {"video", "audio"}
        ]

        if not input_streams:
            raise RuntimeError("No audio/video streams found")

        with av.open(str(temp), mode="w", format="mp4") as output_container:
            output_container.metadata.clear()

            stream_map = {}

            for input_stream in input_streams:
                input_stream.metadata.clear()

                output_stream = output_container.add_stream_from_template(input_stream)
                output_stream.metadata.clear()
                stream_map[input_stream.index] = output_stream

            for packet in input_container.demux(input_streams):
                if packet.dts is None:
                    continue

                mapped_stream = stream_map.get(packet.stream.index)
                if mapped_stream is None:
                    continue

                packet.stream = mapped_stream
                output_container.mux(packet)


def _reencode_video_metadata_free(source: Path, temp: Path) -> None:
    """High-quality fallback re-encode to H.264/AAC."""
    with av.open(str(source), mode="r") as input_container:
        raw_video_stream = next(
            (stream for stream in input_container.streams if stream.type == "video"),
            None,
        )
        raw_audio_stream = next(
            (stream for stream in input_container.streams if stream.type == "audio"),
            None,
        )

        if raw_video_stream is None:
            raise RuntimeError("No video stream found")

        video_stream = cast(VideoStream, raw_video_stream)
        audio_stream = cast(AudioStream, raw_audio_stream) if raw_audio_stream is not None else None

        with av.open(str(temp), mode="w", format="mp4") as output_container:
            output_container.metadata.clear()

            rate = video_stream.average_rate or video_stream.base_rate or 30
            output_video = output_container.add_stream("libx264", rate=rate)
            output_video.width = video_stream.width
            output_video.height = video_stream.height
            output_video.pix_fmt = "yuv420p"
            output_video.options = {
                "crf": "16",
                "preset": "slow",
                "movflags": "+faststart",
            }
            output_video.metadata.clear()

            output_audio = None
            if audio_stream is not None:
                output_audio = output_container.add_stream("aac", rate=audio_stream.rate or 48000)
                output_audio.bit_rate = 320_000
                output_audio.metadata.clear()

            for frame in input_container.decode(video_stream):
                frame.pts = None
                for packet in output_video.encode(frame):
                    output_container.mux(packet)

            for packet in output_video.encode(None):
                output_container.mux(packet)

            if audio_stream is not None and output_audio is not None:
                for frame in input_container.decode(audio_stream):
                    frame.pts = None
                    for packet in output_audio.encode(frame):
                        output_container.mux(packet)

                for packet in output_audio.encode(None):
                    output_container.mux(packet)


def _commit_replacement(*, source: Path, temp: Path, output: Path) -> None:
    """Atomically move temp to output and remove source."""
    if not temp.exists() or temp.stat().st_size <= 0:
        raise RuntimeError(f"Temporary output is missing or empty: {temp}")

    os.replace(temp, output)

    if not output.exists() or output.stat().st_size <= 0:
        raise RuntimeError(f"Output is missing or empty after replace: {output}")

    if source.exists() and source.resolve() != output.resolve():
        source.unlink()


def _cleanup_temp(temp: Path) -> None:
    try:
        if temp.exists():
            temp.unlink()
    except OSError:
        pass
