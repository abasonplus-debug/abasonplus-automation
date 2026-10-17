import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from carousel_timing import validate_timing
class TimingTests(unittest.TestCase):
    def test_variable_count_has_fixed_two_seconds(self):
        for n in (5,8,10,15,25):
            m=dict(slides=n,slide_seconds=2,slide_durations=[2]*n)
            self.assertEqual(validate_timing(m,n*2),n*2)
    def test_three_seconds_and_one_slow_slide_are_rejected(self):
        for ds in ([3]*8,[2]*7+[3],[1.5]*8):
            with self.assertRaises(ValueError):validate_timing(dict(slides=8,slide_seconds=2,slide_durations=ds),16)
    def test_old_fifteen_second_video_and_overlength_rejected(self):
        with self.assertRaises(ValueError):validate_timing(dict(slides=8,slide_seconds=2,slide_durations=[2]*8),15)
        with self.assertRaises(ValueError):validate_timing(dict(slides=26,slide_seconds=2,slide_durations=[2]*26),52)
    def test_real_ffmpeg_concat_changes_frames_at_two_seconds(self):
        import json,subprocess,tempfile,shutil
        from PIL import Image
        if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):self.skipTest('ffmpeg/ffprobe unavailable')
        with tempfile.TemporaryDirectory() as td:
            p=pathlib.Path(td)
            colors=['red','green','blue','yellow','white']
            for i,color in enumerate(colors):Image.new('RGB',(64,64),color).save(p/f'{i}.png')
            manifest=''.join(f"file '{i}.png'\nduration 2\n" for i in range(5))+"file '4.png'\n"
            (p/'slides.txt').write_text(manifest)
            subprocess.run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',str(p/'slides.txt'),'-t','10','-vf','fps=30','-r','30','-c:v','libx264','-pix_fmt','yuv420p',str(p/'test.mp4')],check=True)
            probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(p/'test.mp4')]))
            self.assertEqual(int(probe['streams'][0]['nb_frames']),300)
            validate_timing(dict(slides=5,slide_seconds=2,slide_durations=[2]*5),probe['format']['duration'])
            # Sample centers of each two-second segment, proving actual rendered sequence.
            for i,color in enumerate(colors):
                raw=subprocess.check_output(['ffmpeg','-v','error','-ss',str(i*2+1),'-i',str(p/'test.mp4'),'-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','-'])
                sample=Image.frombytes('RGB',(64,64),raw).getpixel((32,32))
                target=Image.new('RGB',(1,1),color).getpixel((0,0))
                self.assertLess(max(abs(a-b) for a,b in zip(sample,target)),10)
