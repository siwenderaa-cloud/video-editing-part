"""Deterministic self-made action sounds. Python + NumPy; no sampled recordings.

Each style's copy defaults to ../prompts/<demo>/motion_music/Specific_motion_<demo>.
Use --output-root to stage the same per-demo layout in the current project.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import wave
import numpy as np

SR = 48000
PEAK_DBFS = -10.0

SPECS = {
    'bright_paper_storytelling': [
        ('document_dive', 60, [
            ('paper_lift', 'paper_lift.wav', '纸张轻抬与摩擦', 1.45, .50, 45101, 'lift',
             '信息卡从桌面轻抬16px；短促抓纸纹理后接轻摩擦，不配重撞击。'),
            ('confirmation_chime', 'confirmation_chime.wav', '信息就位短铃音', 4.15, .30, 45102, 'chime',
             '右侧128与说明浮显时短确认，声音在4.45秒浮显完成前收束。'),
        ]),
        ('paper_curl', 60, [
            ('paper_curl', 'paper_curl_rustle.wav', '纸页翻卷摩擦', .35, 1.00, 45201, 'curl',
             '主翻卷从0.35到1.35秒的纸背摩擦，先收束再让位给最后收角。'),
            ('paper_edge_settle', 'paper_edge_settle.wav', '末端收角轻触', 1.40, .07, 45202, 'edge',
             '可见折角接近左上端时轻触，1.47秒收束，早于p>=.999时折角移除。'),
        ]),
        ('line_carry', 60, [
            ('camera_sweep', 'camera_sweep.wav', '沿线横移短扫过', 2.10, 1.20, 45301, 'swish',
             '取1.733至3.600秒横移中的主要加速区间，声峰接近2.7秒；不是整段风声。'),
            ('frame_close', 'frame_close_tap.wav', '画面开启轻敲', 4.40, .18, 45302, 'tap',
             '闭框后插画区域开始浮现与展开，单个克制轻敲对齐开启点。'),
        ]),
        ('layer_explode', 60, [
            ('paper_layers', 'paper_layers_rustle.wav', '纸层拉开', .40, 1.35, 45401, 'layers',
             '三层共用0.4至1.75秒展开进度，重叠摩擦纹理随主动作打开，不逐层连续撞击。'),
            ('first_check', 'first_check_tick.wav', '首项确认轻点', 1.80, .16, 45402, 'tick',
             '只在第一条引线与勾线开始时提示一次，后两项保持安静。'),
        ]),
        ('title_layout', 60, [
            ('paper_stamp', 'paper_stamp_tap.wav', '标题纸面压印', 23 / 60, .22, 45501, 'stamp',
             '两行词组压印过程中的首组接触轻点，只提示一次，不给每个字打点。'),
            ('underline_stroke', 'underline_stroke.wav', '下划线短笔划', .75, .70, 45502, 'stroke',
             '下划线从0.75至1.45秒描出，细小干燥摩擦，不添加第二个提示铃。'),
        ]),
    ],
    'dark_pip_explainer': [
        ('dark_pip_explainer', 30, [
            ('comparison_cards_slide', 'comparison_cards_slide.wav', '双卡轻滑入场', 17 / 30, 1.08, 45602, 'cards_slide',
             '从左卡首个可见帧开始，短柔滑过覆盖左卡与右卡先后入场，至约1.65秒收束。'),
            ('question_pop', 'question_soft_pop.wav', '问号柔弹', 2.80, .42, 45601, 'pop',
             '问号缩放与阻尼轻晃开始，短柔弹跟随增长，不叠加重低音或长回声。'),
        ]),
    ],
}

ACTION_WINDOWS = {
    'paper_lift': (1.45, 1.95),
    'confirmation_chime': (4.15, 4.45),
    'paper_curl': (.35, 1.35),
    # io(u) reaches .999 at u=1-cuberoot(.001/4); the fold is then removed.
    'paper_edge_settle': (1.35, .35 + 1.2 * (1 - (.001 / 4) ** (1 / 3))),
    'camera_sweep': (1.733, 3.6),
    'frame_close': (4.4, 5.4),
    'paper_layers': (.4, 1.75),
    'first_check': (1.8, 2.35),
    'paper_stamp': (.08, .70),
    'underline_stroke': (.75, 1.45),
    'comparison_cards_slide': (.55, 1.65),
    'question_pop': (2.8, 3.7),
}

ANCHORS = {
    'paper_lift': {
        'subject': '桌面信息卡中心，由y386抬到y370',
        'coordinate_space': '1280x720 SVG viewBox；下列为桌面组内坐标，尚未施加组的平移/旋转/缩放',
        'point': {'x': 866, 'y': 386}, 'motion_to': {'x': 866, 'y': 370},
        'timing_reason': 'pick=16*out((t-1.45)/.5)，在1.45秒启动，1.95秒轻抬完成；音频覆盖该段摩擦。',
    },
    'confirmation_chime': {
        'subject': '右侧128与信息已就位', 'coordinate_space': '1280x720 SVG viewBox，固定画面坐标',
        'point': {'x': 1090, 'y': 378},
        'timing_reason': '右侧结果在4.15秒开始.25秒淡入与.30秒上移，动作窗口至4.45秒；铃音同点启动且裁为.30秒，完整尾音在浮显结束前收束。',
    },
    'paper_curl': {
        'subject': '纸页右下卷角与斜向折线', 'coordinate_space': '1280x720 SVG viewBox，固定画面坐标',
        'point': {'x': 1120, 'y': 595}, 'page_bounds': {'x': 165, 'y': 212, 'width': 955, 'height': 383},
        'timing_reason': 'p=io((t-.35)/1.2)，主摩擦只取.35至1.35秒阶段；后续末端收角另用极短轻触，两个文件不重叠。',
    },
    'paper_edge_settle': {
        'subject': '纸页左上端最后收角', 'coordinate_space': '1280x720 SVG viewBox，固定画面坐标',
        'point': {'x': 165, 'y': 212}, 'page_bounds': {'x': 165, 'y': 212, 'width': 955, 'height': 383},
        'timing_reason': '源码仅在p<.999绘制旧页与折角，可见截止为.35+1.2*(1-cuberoot(.001/4))≈1.474405秒；取1.40秒/f84轻触.07秒，在1.47秒结束，不借下一页静止停留拖尾。',
    },
    'camera_sweep': {
        'subject': '沿线横移中保持在视野前方的线端', 'coordinate_space': '1280x720 SVG viewBox，已扣除camera横移的画面坐标',
        'point': {'x': 987, 'y': 540},
        'timing_reason': 'camera在1.733至3.600秒以io横移，选2.10至3.30秒主加速部分；声峰约2.70秒接近移镜速度峰值2.6665秒。',
    },
    'frame_close': {
        'subject': '闭框后插画区域开始浮现', 'coordinate_space': '1280x720 SVG viewBox，world坐标减去1280px camera后',
        'point': {'x': 640, 'y': 540}, 'region': {'x': 640, 'y': 210, 'width': 480, 'height': 330},
        'timing_reason': '4.4秒起poster淡入.75秒，圆与两层山形分别在4.55/4.7/4.8秒开始位移，最后至5.4秒；轻敲归属这段实际插画开启动作，非闭框后静止阅读。',
    },
    'paper_layers': {
        'subject': '三层纸面从叠放展开',
        'coordinate_space': '1280x720 SVG viewBox；所列为各纸层变换原点，之后再施加局部rotate/skew/scale与微小camera缩放',
        'origins_start': [{'x': 366, 'y': 390}, {'x': 366, 'y': 397}, {'x': 366, 'y': 404}],
        'origins_end': [{'x': 336, 'y': 280}, {'x': 336, 'y': 395}, {'x': 336, 'y': 510}],
        'timing_reason': '三层共用p=io((t-.4)/1.35)，.4至1.75秒同时展开；单个重叠纸声覆盖该动作，不逐层加撞击。',
    },
    'first_check': {
        'subject': '第一条引线旁的勾线', 'coordinate_space': '1280x720 SVG viewBox；点在微小camera缩放之前',
        'point': {'x': 871, 'y': 260},
        'timing_reason': '第一项q=ramp(t,1.8,.55)开始；首项提示一次，第二/第三项不重复加声。',
    },
    'paper_stamp': {
        'subject': '两行标题词组共同压印，首组接触提示', 'coordinate_space': '1280x720 SVG viewBox，固定画面坐标',
        'point': {'x': 410, 'y': 335},
        'related_points': [{'x': 410, 'y': 335}, {'x': 410, 'y': 438}],
        'timing_reason': '所选动作为两行标题的整体词组压印，实际窗口.08至.70秒；在首组接触f23=.383333秒提示一次，.22秒声音结束时第二行仍在完成压印，不扩展到阅读停留。',
    },
    'underline_stroke': {
        'subject': '标题下方描出的橘色下划线', 'coordinate_space': '1280x720 SVG viewBox，固定画面坐标',
        'path_start': {'x': 412, 'y': 468}, 'path_end': {'x': 947, 'y': 467},
        'timing_reason': 'Rule的进度ramp(t,.75,.7)，.75至1.45秒描出；笔划声与该.7秒窗口一致。',
    },
    'comparison_cards_slide': {
        'subject': '左右对比卡共同的向上14px入场', 'coordinate_space': '1280x720 SVG viewBox，固定画面坐标',
        'regions': [{'x': 334, 'y': 254, 'width': 364, 'height': 268}, {'x': 740, 'y': 254, 'width': 364, 'height': 268}],
        'timing_reason': '左卡从.55秒开始，30fps首个可见帧f17=.566667秒；右卡从.85秒开始至1.65秒到位，音频持续1.08秒覆盖两卡先后进入。',
    },
    'question_pop': {
        'subject': '中央问号缩放与阻尼轻晃的中心', 'coordinate_space': '1280x720 SVG viewBox，固定画面坐标',
        'point': {'x': 640, 'y': 422},
        'timing_reason': 'elapsed=max(0,t-2.8)，问号在2.8秒开始增长并轻晃；柔弹同点启动，不在文字停留时反复响。',
    },
}


def band_noise(rng, count, low, high, tilt=0.0):
    """FFT-coloured noise with smooth band edges; no source audio samples."""
    f = np.fft.rfftfreq(count, 1 / SR)
    spectrum = np.fft.rfft(rng.standard_normal(count))
    lo = np.clip((f - low) / max(100, low * .5), 0, 1)
    hi = np.clip((high - f) / max(300, high * .18), 0, 1)
    mask = np.sin(lo * np.pi / 2) ** 2 * np.sin(hi * np.pi / 2) ** 2
    mask *= (np.maximum(f, low) / max(low, 1)) ** tilt
    signal = np.fft.irfft(spectrum * mask, n=count)
    return signal / max(np.std(signal), 1e-12)


def shaped_burst(t, center, width):
    return np.exp(-.5 * ((t - center) / width) ** 2)


def synth(kind, duration, seed):
    rng = np.random.default_rng(seed)
    count = round(duration * SR)
    t = np.arange(count) / SR
    u = t / duration
    paper = band_noise(rng, count, 550, 8900, -.13)
    grain = band_noise(rng, count, 2400, 13000, -.25)
    low = band_noise(rng, count, 110, 2200, -.30)
    params = {'kind': kind, 'seed': seed, 'sample_rate': SR, 'duration_seconds': duration,
              'peak_dbfs': PEAK_DBFS, 'end_fade_seconds': min(.025, duration / 6)}

    if kind in ('lift', 'curl', 'layers', 'stroke'):
        # Moving paper: broadband fibre friction plus sparse crinkles. No pitched beep.
        nodes = rng.uniform(.35, 1, max(6, round(duration * 33)))
        motion = np.interp(t, np.linspace(0, duration, len(nodes)), nodes)
        envelope = np.sin(np.pi * np.clip(u, 0, 1)) ** .8
        if kind == 'lift':
            envelope = (.55 * shaped_burst(t, .07, .038) + .42 * shaped_burst(t, .27, .14))
            x = paper * motion * envelope + .12 * grain * shaped_burst(t, .035, .009)
            params.update(noise_bands_hz=[[550, 8900], [2400, 13000]], friction_peaks_seconds=[.07, .27])
        elif kind == 'curl':
            envelope = np.sin(np.pi * np.clip(u, 0, 1)) ** 1.25
            crinkles = sum(shaped_burst(t, c, w) * a for c, w, a in [(.21, .012, .13), (.51, .02, .18), (.83, .013, .10)])
            x = paper * motion * envelope + grain * crinkles + .13 * low * envelope
            params.update(noise_bands_hz=[[550, 8900], [2400, 13000], [110, 2200]],
                          crinkle_centers_seconds=[.21, .51, .83], envelope='sin(pi*t/duration)^1.25')
        elif kind == 'layers':
            texture = .62 * paper + .23 * np.roll(paper, 1200) + .15 * np.roll(grain, 2640)
            x = texture * motion * envelope + .10 * low * envelope
            params.update(noise_bands_hz=[[550, 8900], [2400, 13000], [110, 2200]],
                          texture_delays_seconds=[0, .025, .055], envelope='sin(pi*t/duration)^0.8')
        else:
            envelope = (.28 + .72 * np.exp(-t / .20)) * (1 - np.exp(-t / .008))
            scratch = .75 + .25 * np.sin(2 * np.pi * (14 * t + 5 * t * t))
            x = .64 * grain * motion * envelope * scratch + .26 * paper * envelope
            params.update(noise_bands_hz=[[2400, 13000], [550, 8900]], scratch_modulation_hz='14+10t',
                          envelope='(.28+.72*exp(-t/.20))*(1-exp(-t/.008))')
    elif kind in ('tap', 'stamp', 'tick'):
        # Contact transient + rapidly damped wood/paper body; deliberately non-musical.
        contact_tau = {'tap': .012, 'stamp': .022, 'tick': .009}[kind]
        body = sum(a * np.sin(2 * np.pi * f * t + phase) * np.exp(-t / tau)
                   for f, a, tau, phase in [(182, .50, .038, 0), (363, .25, .026, .45), (794, .15, .019, .9)])
        x = .62 * paper * np.exp(-t / contact_tau) + .14 * grain * np.exp(-t / .006) + body
        if kind == 'stamp':
            x += .36 * low * np.exp(-t / .045) + .22 * paper * shaped_burst(t, .042, .018)
        if kind == 'tick':
            x = .65 * x + .12 * grain * np.exp(-t / .016)
        params.update(noise_bands_hz=[[550, 8900], [2400, 13000]], contact_decay_seconds=contact_tau,
                      resonances_hz=[182, 363, 794], resonance_decays_seconds=[.038, .026, .019])
    elif kind == 'edge':
        x = (.72 * paper * np.exp(-t / .014) + .20 * grain * np.exp(-t / .006)
             + .14 * low * np.exp(-t / .024) + .24 * paper * shaped_burst(t, .031, .009))
        params.update(noise_bands_hz=[[550, 8900], [2400, 13000], [110, 2200]],
                      band_amplitudes=[.72, .20, .14], contact_decays_seconds=[.014, .006, .024],
                      paper_flap_center_seconds=.031, paper_flap_width_seconds=.009, paper_flap_amplitude=.24)
    elif kind == 'cards_slide':
        env = (.62 * shaped_burst(t, .19, .15) + .43 * shaped_burst(t, .49, .18))
        x = (.30 * low + .55 * paper + .12 * grain) * env
        params.update(noise_bands_hz=[[110, 2200], [550, 8900], [2400, 13000]],
                      band_amplitudes=[.30, .55, .12], movement_peak_centers_seconds=[.19, .49],
                      movement_peak_widths_seconds=[.15, .18], movement_peak_amplitudes=[.62, .43])
    elif kind == 'swish':
        env = np.sin(np.pi * np.clip(u, 0, 1)) ** 1.8
        x = (.60 * low * (1 - u) + .32 * paper + .36 * grain * u) * env
        params.update(noise_bands_hz=[[110, 2200], [550, 8900], [2400, 13000]],
                      envelope='sin(pi*t/duration)^1.8', timbre='low-to-high friction sweep')
    elif kind == 'chime':
        # Small bell-inspired inharmonic modal decay, with one subdued secondary tap.
        ratios, amps, decays = [1, 2.76, 5.4, 8.93], [1, .40, .18, .07], [.19, .13, .085, .055]
        x = np.zeros(count)
        for offset, velocity in [(0, 1), (.18, .20)]:
            local = np.maximum(0, t - offset)
            gate = t >= offset
            for ratio, amp, decay in zip(ratios, amps, decays):
                x += velocity * amp * np.sin(2 * np.pi * 1046.5 * ratio * local) * np.exp(-local / decay) * (1 - np.exp(-local / .0015)) * gate
        params.update(fundamental_hz=1046.5, partial_ratios=ratios, partial_amplitudes=amps,
                      decay_seconds=decays, strikes_seconds=[0, .18], strike_velocities=[1, .20])
    elif kind == 'pop':
        phase = 2 * np.pi * (260 * t - 110 * t * t)
        env = (1 - np.exp(-t / .018)) * np.exp(-t / .09)
        x = (.75 * np.sin(phase) + .12 * np.sin(phase * 1.42) + .05 * np.sin(phase * 2.7)) * env
        x += .13 * low * shaped_burst(t, .03, .018)
        params.update(instantaneous_fundamental_hz='260-220t', partial_ratios=[1, 1.42, 2.7],
                      attack_seconds=.018, decay_seconds=.09, contact_burst_seconds=.03)
    else:
        raise ValueError(kind)

    # Smooth file boundaries, remove DC without moving endpoints, then set safe headroom.
    attack = .0018 if kind in ('tap', 'stamp', 'tick') else .004
    params['boundary_envelope'] = {
        'attack_seconds': attack, 'release_seconds': min(.025, duration / 6),
        'attack_formula': 'sin(clamp(t/attack,0,1)*pi/2)^2',
        'release_formula': 'sin(clamp((duration-1/SR-t)/release,0,1)*pi/2)^2',
        'dc_correction': 'subtract mean(x)/mean(sin(pi*u)^2)*sin(pi*u)^2',
        'normalization': 'normalize largest absolute sample to -10dBFS; force first and last samples to zero',
    }
    fade_in = np.sin(np.clip(t / attack, 0, 1) * np.pi / 2) ** 2
    fade_out = np.sin(np.clip((duration - 1 / SR - t) / min(.025, duration / 6), 0, 1) * np.pi / 2) ** 2
    x *= fade_in * fade_out
    dc_window = np.sin(np.pi * np.linspace(0, 1, count)) ** 2
    x -= np.mean(x) / np.mean(dc_window) * dc_window
    x *= 10 ** (PEAK_DBFS / 20) / max(np.max(np.abs(x)), 1e-12)
    x[0] = x[-1] = 0
    return np.rint(x * 32767).astype('<i2'), params


def create(style, output_root):
    assert style in SPECS, style
    output_root.mkdir(parents=True, exist_ok=True)
    rows = []
    for demo, fps, sounds in SPECS[style]:
        prompt_stem = f'Specific_motion_{demo}'
        folder = output_root / demo / 'motion_music' / prompt_stem
        folder.mkdir(parents=True, exist_ok=True)
        assert len(sounds) <= 5
        manifest = {'demo_id': demo, 'prompt_file': prompt_stem + '.md',
                    'silent_prompt_file': f'None_Specific_motion_{demo}.md', 'fps': fps,
                    'source': 'self_made', 'synthesis': 'deterministic procedural synthesis; no recorded samples',
                    'format': {'sample_rate': SR, 'channels': 1, 'codec': 'PCM signed 16-bit WAV'},
                    'default_demo_audio': 'off; silent standalone reference video keeps no audio track; optional sound demo uses cue gain_db',
                    'selection_rule': '0 to 5 sounds per prompt, usually 2 to 3 when useful; select action anchors rather than filling a quota',
                    'action_frame_rule': 'ceil(action_seconds*fps); end frame is exclusive; continuous action seconds remain authoritative',
                    'cues': []}
        previous_end = 0.0
        for sound_id, filename, label, start, duration, seed, kind, action in sounds:
            assert 0 < duration <= 1.5
            action_start, action_end = ACTION_WINDOWS[sound_id]
            assert action_start <= start + 1e-9 and start + duration <= action_end + 1e-9
            assert start >= previous_end - 1e-9, 'Selected motion sound files must not overlap'
            previous_end = start + duration
            pcm, params = synth(kind, duration, seed)
            path = folder / filename
            with wave.open(str(path), 'wb') as out:
                out.setnchannels(1)
                out.setsampwidth(2)
                out.setframerate(SR)
                out.writeframes(pcm.tobytes())
            cue = {'id': sound_id, 'file': filename, 'label': label,
                   'start_seconds': round(start, 6), 'frame': round(start * fps),
                   'end_seconds': round(start + duration, 6),
                   'action_start_seconds': action_start, 'action_end_seconds': action_end,
                   'action_start_frame': math.ceil(action_start * fps - 1e-9),
                   'action_end_frame_exclusive': math.ceil(action_end * fps - 1e-9),
                   'duration_seconds': duration, 'gain_db': -6, 'suggested_mix_gain_db': -12,
                   'action': action, 'description': 'Physical-action-inspired synthesized sound; not a live recording.',
                   'visual_anchor': {k: v for k, v in ANCHORS[sound_id].items() if k != 'timing_reason'},
                   'timing_reason': ANCHORS[sound_id]['timing_reason'],
                   'parameters': params, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
            manifest['cues'].append(cue)
            rows.append({'demo': demo, **cue})
        (folder / 'cue.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    style_dir = Path(__file__).resolve().parents[1]
    parser.add_argument('--style', choices=SPECS, default=style_dir.name)
    parser.add_argument('--output-root', type=Path, default=style_dir / 'prompts')
    args = parser.parse_args()
    rows = create(args.style, args.output_root)
    print(json.dumps({'style': args.style, 'audio_files': len(rows), 'output_root': str(args.output_root)}, ensure_ascii=False))
