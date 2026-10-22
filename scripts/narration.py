"""Local Bengali narration. No API, subscription, credentials or telemetry.

eSpeak NG is free GPL software. Its synthetic voice is not claimed to sound human.
"""
import hashlib
import json
import math
from pathlib import Path
import subprocess
import wave

def wave_seconds(path):
    with wave.open(str(path),'rb') as wav:
        if wav.getnchannels()!=1 or wav.getsampwidth()!=2 or wav.getframerate()<16000:
            raise ValueError('Invalid narration PCM format')
        seconds=wav.getnframes()/wav.getframerate()
        frames=wav.readframes(wav.getnframes())
        if not frames or not any(frames) or seconds<=0:
            raise ValueError('Empty/silent narration')
        return seconds

def prepare(texts, out):
    out=Path(out)
    measured=[];durations=[]
    for i,text in enumerate(texts):
        if not isinstance(text,str) or not text.strip() or len(text)>500:
            raise ValueError('Narration needs the exact bounded slide script')
        path=out/f'narration_{i}.wav'
        subprocess.run(['espeak-ng','-v','bn','-s','145','-w',str(path),'--stdin'],
                       input=text, text=True, check=True, timeout=90, capture_output=True)
        length=wave_seconds(path)
        measured.append(length)
        durations.append(math.ceil((length+.4)*30)/30)
    # Pad each spoken segment to its slide boundary; never accelerate/cut speech.
    for i,duration in enumerate(durations):
        subprocess.run(['ffmpeg','-v','error','-y','-i',str(out/f'narration_{i}.wav'),
                        '-af','apad','-t',str(duration),'-ar','22050','-ac','1',
                        str(out/f'narration_padded_{i}.wav')],check=True,timeout=90,capture_output=True)
    playlist=out/'narration.txt'
    playlist.write_text(''.join(f"file 'narration_padded_{i}.wav'\n" for i in range(len(texts))))
    voice=out/'narration.wav'
    subprocess.run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',str(playlist),
                    '-c:a','pcm_s16le',str(voice)],check=True,timeout=90,capture_output=True)
    evidence={'engine':'espeak-ng-bn','script_sha256':hashlib.sha256('\n'.join(texts).encode()).hexdigest(),
              'sha256':hashlib.sha256(voice.read_bytes()).hexdigest(),'segment_seconds':measured,
              'slide_durations':durations,'voice_quality':'synthetic_not_human_reviewed'}
    (out/'narration.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n')
    return evidence

def verify(meta, brief, out):
    out=Path(out)
    evidence=meta.get('narration',{})
    texts=[brief['hook']]+[p['text'] for p in brief['tips']]
    script_hash=hashlib.sha256('\n'.join(texts).encode()).hexdigest()
    if evidence.get('script_sha256')!=script_hash:
        raise ValueError('Narration script differs from exact slide text')
    voice=out/'narration.wav'
    if not voice.is_file() or hashlib.sha256(voice.read_bytes()).hexdigest()!=evidence.get('sha256'):
        raise ValueError('Narration WAV missing or changed')
    length=wave_seconds(voice)
    if abs(length-sum(meta['slide_durations']))>.15:
        raise ValueError('Narration padding differs from slide boundaries')
    return True
