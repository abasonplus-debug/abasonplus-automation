import pathlib,sys,unittest,json
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from carousel_timing import validate_timing,SLIDE_SECONDS,MIN_SLIDES,MAX_SLIDES

class TimingTests(unittest.TestCase):
    def test_variable_count_has_fixed_three_seconds(self):
        for n in (5,8,10,15,16):
            m=dict(slides=n,slide_seconds=3,slide_durations=[3]*n)
            self.assertEqual(validate_timing(m,n*3),n*3)
        self.assertEqual(MAX_SLIDES,16)

    def test_full_script_length_ignores_former_fifty_second_limit(self):
        for times in ([12.5]*5, [120.0]*5, [45.0]*16):
            count = len(times)
            meta = dict(slides=count, slide_seconds=3, slide_durations=times,
                        voiceover=dict(complete=True, engine="CosyVoice3",
                                       reference="Dan Mason", narrated_slide_count=count))
            self.assertEqual(validate_timing(meta, sum(times)),sum(times))
        with self.assertRaises(ValueError):
            validate_timing(dict(slides=5,slide_seconds=3,slide_durations=[10]*5),50)

    def test_old_or_mixed_slide_timing_is_rejected(self):
        for seconds,ds in ((2,[2]*8),(3,[3]*7+[2]),(3,[1.5]*8),(3,[3]*7+[4])):
            with self.assertRaises(ValueError):
                validate_timing(dict(slides=8,slide_seconds=seconds,slide_durations=ds),24)

    def test_duration_and_count_limits_fail_closed(self):
        with self.assertRaises(ValueError):
            validate_timing(dict(slides=8,slide_seconds=3,slide_durations=[3]*8),16)
        for n in (4,17,25,True):
            with self.assertRaises(ValueError):
                validate_timing(dict(slides=n,slide_seconds=3,slide_durations=[3]*int(n)))

    def test_visual_contract_matches_timing(self):
        root=pathlib.Path(__file__).resolve().parents[1]
        policy=json.loads((root/'config/carousel_style.json').read_text())
        self.assertEqual((policy['slide_seconds'],policy['min_slides'],policy['max_slides']),
                         (SLIDE_SECONDS,MIN_SLIDES,MAX_SLIDES))

    def test_real_ffmpeg_concat_changes_frames_at_three_seconds(self):
        import subprocess,tempfile,shutil
        from PIL import Image
        if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
            self.skipTest('ffmpeg/ffprobe unavailable')
        with tempfile.TemporaryDirectory() as td:
            p=pathlib.Path(td)
            colors=['red','green','blue','yellow','white']
            for i,color in enumerate(colors):
                Image.new('RGB',(64,64),color).save(p/f'{i}.png')
            manifest=''.join(f"file '{i}.png'\nduration 3\n" for i in range(5))+"file '4.png'\n"
            (p/'slides.txt').write_text(manifest)
            subprocess.run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',str(p/'slides.txt'),
                            '-t','15','-vf','fps=30','-r','30','-c:v','libx264','-pix_fmt','yuv420p',
                            str(p/'test.mp4')],check=True)
            probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams',
                                                       '-of','json',str(p/'test.mp4')]))
            self.assertEqual(int(probe['streams'][0]['nb_frames']),450)
            validate_timing(dict(slides=5,slide_seconds=3,slide_durations=[3]*5),probe['format']['duration'])
            # Check immediately before and after every actual slide boundary.
            for t,index in [(i*3+1.5,i) for i in range(5)]+[(i*3-0.1,i-1) for i in range(1,5)]+[(i*3+0.1,i) for i in range(1,5)]:
                raw=subprocess.check_output(['ffmpeg','-v','error','-ss',str(t),'-i',str(p/'test.mp4'),
                                             '-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','-'])
                sample=Image.frombytes('RGB',(64,64),raw).getpixel((32,32))
                target=Image.new('RGB',(1,1),colors[index]).getpixel((0,0))
                self.assertLess(max(abs(a-b) for a,b in zip(sample,target)),10)
