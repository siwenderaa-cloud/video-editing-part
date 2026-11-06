"""Copy a silent demo's video stream and mix its selected short motion sounds.

Requires Python 3.10+, ffmpeg and ffprobe on PATH. No third-party Python packages.
"""
from pathlib import Path
from fractions import Fraction
import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import tempfile
import wave

RATE = 48000
MAX_CUES = 5
STYLE = Path(__file__).resolve().parent.parent
PROTECTED = STYLE.parent.resolve() if STYLE.parent.name == 'realization_demo' else STYLE.resolve()


def run(command):
    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if result.returncode:
        raise RuntimeError(f'{command[0]} failed:\n{result.stderr[-4000:]}')
    return result.stdout, result.stderr


def probe(path):
    output, _ = run(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)])
    return json.loads(output)


def video_hash(path):
    output, _ = run(['ffmpeg', '-nostdin', '-v', 'error', '-i', str(path), '-map', '0:v:0',
                     '-c:v', 'copy', '-f', 'hash', '-hash', 'sha256', '-'])
    return output.strip().split('=', 1)[1]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def finite_number(value, label):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f'{label} must be finite')
    return number


def render(demo_id, output, work=None):
    if not re.fullmatch(r'[a-z][a-z0-9_]*', demo_id):
        raise ValueError('demo must be a simple snake_case identifier')
    cue_file = STYLE / 'prompts' / demo_id / 'motion_music' / f'Specific_motion_{demo_id}' / 'cue.json'
    base = STYLE / 'assets' / demo_id / 'silent.mp4'
    if not base.is_file() or not cue_file.is_file():
        raise FileNotFoundError(f'Demo or cue file does not exist: {demo_id}')
    output = output.resolve()
    if output.suffix.lower() != '.mp4' or output.is_relative_to(PROTECTED):
        raise ValueError('Choose an explicit .mp4 output outside the demo library, in your current project')
    if work:
        work = work.resolve()
        if work.is_relative_to(PROTECTED):
            raise ValueError('Work logs must be outside the demo library')
        work.mkdir(parents=True, exist_ok=True)

    metadata = json.loads(cue_file.read_text(encoding='utf-8-sig'))
    if metadata.get('demo_id') != demo_id:
        raise ValueError('cue.json demo_id differs from --demo')
    if metadata.get('prompt_file') != f'Specific_motion_{demo_id}.md':
        raise ValueError('cue.json must belong to the matching sound prompt')
    cues = metadata.get('cues')
    if not isinstance(cues, list) or len(cues) > MAX_CUES:
        raise ValueError(f'cue.json must contain 0 to {MAX_CUES} selected motion sounds')
    source = probe(base)
    videos = [s for s in source['streams'] if s['codec_type'] == 'video']
    if len(videos) != 1 or any(s['codec_type'] == 'audio' for s in source['streams']):
        raise ValueError('Base demo must contain one video stream and zero audio streams')
    video = videos[0]
    fps = Fraction(video['avg_frame_rate'])
    seconds = finite_number(video.get('duration', source['format']['duration']), 'base duration')
    frames = int(video['nb_frames'])
    if frames <= 0 or seconds <= 0 or abs(frames / float(fps) - seconds) > .025:
        raise ValueError('Base duration and frame count are inconsistent')
    if abs(finite_number(metadata['fps'], 'cue fps') - float(fps)) > 1e-6:
        raise ValueError('cue.json fps differs from the base demo')
    total_samples = round(seconds * RATE)
    sounds = []
    for cue in cues:
        path = (cue_file.parent / cue['file']).resolve()
        if not path.is_relative_to(cue_file.parent.resolve()) or path.suffix.lower() != '.wav':
            raise ValueError('Each cue must reference a WAV inside its own prompt sound folder')
        with wave.open(str(path), 'rb') as wav:
            wav_frames, channels, sample_rate = wav.getnframes(), wav.getnchannels(), wav.getframerate()
            duration = wav_frames / sample_rate
            if sample_rate != RATE or channels not in (1, 2) or wav.getsampwidth() != 2:
                raise ValueError(f'{path.name}: expected 48kHz mono/stereo PCM16 WAV')
            if not 0 < duration <= 1.5:
                raise ValueError(f'{path.name}: each sound must be longer than 0 and at most 1.5 seconds')
            if len(wav.readframes(wav_frames)) != wav_frames * channels * 2:
                raise ValueError(f'{path.name}: truncated PCM data')
        if abs(finite_number(cue['duration_seconds'], 'cue duration') - duration) > 1.1 / RATE:
            raise ValueError(f'{path.name}: declared duration differs from actual WAV')
        start = finite_number(cue['start_seconds'], 'cue start')
        frame = cue['frame']
        if not isinstance(frame, int) or not 0 <= frame < frames or frame != round(start * float(fps)):
            raise ValueError(f'{path.name}: trigger frame/time mismatch or out of range')
        if start < 0 or start + duration > seconds + .5 / RATE:
            raise ValueError(f'{path.name}: sound extends beyond the demo')
        action_start = finite_number(cue['action_start_seconds'], 'action start')
        action_end = finite_number(cue['action_end_seconds'], 'action end')
        if not 0 <= action_start < action_end <= seconds:
            raise ValueError(f'{path.name}: invalid visible-action window')
        if (cue['action_start_frame'] != math.ceil(action_start * float(fps) - 1e-9)
                or cue['action_end_frame_exclusive'] != math.ceil(action_end * float(fps) - 1e-9)):
            raise ValueError(f'{path.name}: action frame limits must use ceil; end is exclusive')
        if start < action_start - 1e-9 or start + duration > action_end + 1e-9:
            raise ValueError(f'{path.name}: complete sound, including tail, must stay inside its visible-action window')
        if abs(finite_number(cue['end_seconds'], 'cue end') - (start + duration)) > .5 / RATE:
            raise ValueError(f'{path.name}: declared sound end differs from file duration')
        gain = finite_number(cue['gain_db'], 'cue gain')
        digest = sha256(path)
        if cue.get('sha256') and cue['sha256'] != digest:
            raise ValueError(f'{path.name}: WAV hash differs from cue.json')
        sounds.append({'path': path, 'id': cue['id'], 'start_seconds': start,
                       'start_samples': round(start * RATE), 'frame': frame, 'gain_db': gain,
                       'end_seconds': start + duration,
                       'action_start_seconds': action_start, 'action_end_seconds': action_end,
                       'action_start_frame': cue['action_start_frame'],
                       'action_end_frame_exclusive': cue['action_end_frame_exclusive'],
                       'duration_seconds': duration, 'channels': channels, 'sha256': digest})
    sounds.sort(key=lambda s: s['start_samples'])
    for earlier, later in zip(sounds, sounds[1:]):
        if earlier['end_seconds'] > later['start_seconds'] + 1e-9:
            raise ValueError('Selected short sound files must not overlap each other')

    output.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=f'.{output.stem}_', suffix='.mp4', dir=output.parent)
    os.close(handle)
    staged = Path(temporary)
    try:
        command = ['ffmpeg', '-nostdin', '-hide_banner', '-v', 'error', '-xerror', '-y', '-i', str(base),
                   '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo']
        filters = [f'[1:a]atrim=end_sample={total_samples},asetpts=PTS-STARTPTS[a0]']
        for index, sound in enumerate(sounds, 2):
            command += ['-i', str(sound['path'])]
            layout = ('aformat=sample_fmts=fltp:sample_rates=48000,pan=stereo|c0=c0|c1=c0'
                      if sound['channels'] == 1 else
                      'aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo')
            filters.append(f'[{index}:a]{layout},'
                           f'volume={sound["gain_db"]}dB,adelay={sound["start_samples"]}S:all=1,'
                           f'apad=whole_len={total_samples},atrim=end_sample={total_samples}[a{index-1}]')
        labels = ''.join(f'[a{i}]' for i in range(len(sounds) + 1))
        filters.append(f'{labels}amix=inputs={len(sounds)+1}:normalize=0:duration=longest:dropout_transition=0,'
                       f'atrim=end_sample={total_samples},asetpts=PTS-STARTPTS[mix]')
        command += ['-filter_complex', ';'.join(filters), '-map', '0:v:0', '-map', '[mix]',
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ar', str(RATE), '-ac', '2',
                    '-t', f'{seconds:.9f}', '-movflags', '+faststart', str(staged)]
        _, mix_log = run(command)
        final = probe(staged)
        final_video = next(s for s in final['streams'] if s['codec_type'] == 'video')
        audios = [s for s in final['streams'] if s['codec_type'] == 'audio']
        if len(audios) != 1 or audios[0]['codec_name'] != 'aac' or int(audios[0]['sample_rate']) != RATE or audios[0]['channels'] != 2:
            raise RuntimeError('Export audio format differs from 48kHz stereo AAC')
        for field in ['width', 'height', 'avg_frame_rate', 'nb_frames']:
            if final_video[field] != video[field]:
                raise RuntimeError(f'Export changed video field: {field}')
        if abs(float(final['format']['duration']) - seconds) > .025:
            raise RuntimeError('Export duration differs from the base demo')
        source_video_hash, final_video_hash = video_hash(base), video_hash(staged)
        if source_video_hash != final_video_hash:
            raise RuntimeError('Video stream was not copied byte-for-byte')
        _, decode_log = run(['ffmpeg', '-nostdin', '-v', 'error', '-xerror', '-i', str(staged), '-f', 'null', '-'])
        _, peak_log = run(['ffmpeg', '-nostdin', '-hide_banner', '-i', str(staged), '-vn',
                           '-af', 'loudnorm=I=-16:TP=-1:LRA=11:print_format=json', '-f', 'null', '-'])
        peak_data = json.loads(re.findall(r'\{[^{}]*"input_tp"[^{}]*\}', peak_log)[-1])
        true_peak = float(peak_data['input_tp'])
        if true_peak > -1:
            raise RuntimeError(f'AAC decoded true peak {true_peak}dBTP exceeds -1dBTP; lower cue gain_db and retry')
        # Only publish after every check succeeds; source files are never modified.
        os.replace(staged, output)
        report = {'status': 'passed', 'demo_id': demo_id, 'style': STYLE.name, 'base': str(base),
                  'output': str(output), 'seconds': seconds, 'fps': str(fps), 'frames': frames,
                  'dimensions': [video['width'], video['height']], 'cue_file': str(cue_file),
                  'cue_file_sha256': sha256(cue_file), 'cues': [{**s, 'path': str(s['path'])} for s in sounds],
                  'audio': {'codec': 'AAC', 'sample_rate': RATE, 'channels': 2, 'target_bitrate': 192000,
                            'decoded_true_peak_dbTP': true_peak if math.isfinite(true_peak) else '-inf', 'bgm_or_voice': False},
                  'video_stream_copy_sha256': final_video_hash, 'video_stream_matches_base': True,
                  'base_sha256': sha256(base), 'output_sha256': sha256(output), 'full_decode': 'passed',
                  'additional_fades': False, 'amix_normalize': 0, 'sample_exact_delays': True}
        report['visible_action_window_check'] = 'passed; continuous seconds authoritative, frame bounds use ceil'
        report['non_overlapping_sound_files'] = True
        report['mono_to_stereo'] = 'pan=stereo|c0=c0|c1=c0 (unity gain to each channel)'
        if work:
            (work / 'mix_command.json').write_text(json.dumps(command, ensure_ascii=False, indent=2), encoding='utf-8')
            (work / 'ffmpeg_mix.log').write_text(mix_log, encoding='utf-8')
            (work / 'full_decode.log').write_text(decode_log, encoding='utf-8')
            (work / 'aac_peak.log').write_text(peak_log, encoding='utf-8')
            (work / 'validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        return report
    finally:
        if staged.exists():
            staged.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo', required=True, help='Demo snake_case id, matching its cue.json')
    parser.add_argument('--output', required=True, type=Path, help='Explicit .mp4 destination in the current project')
    parser.add_argument('--work', type=Path, help='Optional current-project process directory for logs and validation')
    args = parser.parse_args()
    report = render(args.demo, args.output, args.work)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
