"""Compile actual active-workflow Python heredocs, not just separate .py files."""
import pathlib,re,unittest,yaml
ROOT=pathlib.Path(__file__).resolve().parents[1]
class WorkflowPython(unittest.TestCase):
    def test_active_inline_python_syntax(self):
        count=0
        for name in ['daily-carousel.yml','tiktok-publish-reviewed.yml','wordpress-post.yml']:
            data=yaml.safe_load((ROOT/'.github/workflows'/name).read_text())
            for job in data['jobs'].values():
                for step in job.get('steps',[]):
                    script=step.get('run','')
                    for match in re.finditer(r"python(?:3)? - <<['\"]?(\w+)['\"]?\n(.*?)\n\1(?:\n|$)",script,re.S):
                        count+=1
                        with self.subTest(workflow=name,step=step.get('name')):
                            compile(match.group(2),name+':'+step.get('name','inline'),'exec')
        self.assertGreaterEqual(count,4)
