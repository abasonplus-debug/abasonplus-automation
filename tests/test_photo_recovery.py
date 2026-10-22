import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from photo_preflight import candidates, download, readable_crop, select

class Guard:
    def __init__(self, approved=True): self.accept=approved
    def approved(self, image, query): return self.accept

def photo(n=1):
    return {'url':f'https://images.pexels.com/photos/{n}/photo.jpg',
            'source_page':f'https://www.pexels.com/photo/road-{n}/',
            'creator':'Fixture', 'license':'Pexels Free License', 'scene':'Road', 'scene_match':'Road topic'}

class PhotoRecovery(unittest.TestCase):
    def test_crop_repairs_busy_center_without_changing_threshold(self):
        im=Image.new('RGB',(4000,2000),'gray')
        # First center fails; the next natural crop succeeds under unchanged gate.
        with patch('photo_preflight.photo_stats',side_effect=[[[100,20,68]],[[100,20,4]]]):
            _,_,center=readable_crop(im,[[(100,400,900,600)]],'road',Guard())
        self.assertEqual(center,[0,.5])

    def test_semantic_failure_never_passes_readable_crop(self):
        with self.assertRaises(ValueError):
            readable_crop(Image.new('RGB',(1600,2000),'gray'),[[(100,400,900,600)]],'road',Guard(False))

    def test_verified_alternative_and_attribution(self):
        p=photo();p['alternatives']=[photo(2)]
        def loader(url):
            if '/1/' in url: raise RuntimeError('Photograph HTTP 403')
            return Image.new('RGB',(1600,2000),'gray')
        used=set();_,_,chosen,evidence=select(p,[[(100,400,900,600)]],'road',Guard(),used,loader)
        self.assertEqual(chosen['creator'],'Fixture');self.assertEqual(evidence['candidate'],1)
        self.assertEqual(len(used),1)

    def test_no_duplicate_by_query_variant(self):
        p=photo();p['url']+='?size=large'
        with self.assertRaises(RuntimeError):
            select(p,[[]],'road',Guard(),{'/photos/1/photo.jpg'},lambda _:None)

    def test_unverified_or_conflicting_alternatives_rejected(self):
        for field,value in [('license','Unknown'),('source_page','http://www.pexels.com/photo/x/'),('scene_match','')]:
            p=photo();alt=photo(2);alt[field]=value;p['alternatives']=[alt]
            with self.assertRaises(ValueError): candidates(p)
        p=photo();p['source']='https://www.pexels.com/photo/different/'
        with self.assertRaises(ValueError): candidates(p)

    def test_permanent_403_not_retried(self):
        calls=[]
        def opener(req,timeout): calls.append(1);raise HTTPError(req.full_url,403,'Forbidden',{},None)
        with self.assertRaisesRegex(RuntimeError,'403'): download(photo()['url'],opener,lambda _:None)
        self.assertEqual(len(calls),1)

    def test_5xx_bounded_backoff(self):
        calls=[];waits=[]
        def opener(req,timeout): calls.append(1);raise HTTPError(req.full_url,503,'Unavailable',{},None)
        with self.assertRaises(RuntimeError):download(photo()['url'],opener,waits.append)
        self.assertEqual(len(calls),3);self.assertEqual(waits,[1,2])

    def test_onnx_telemetry_disabled_before_model_initialization(self):
        import ast
        root=Path(__file__).resolve().parents[1]
        tree=ast.parse((root/'scripts/photo_relevance.py').read_text())
        init=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='__init__')
        calls=[n for n in ast.walk(init) if isinstance(n,ast.Call)]
        disable=next(n.lineno for n in calls if isinstance(n.func,ast.Attribute) and n.func.attr=='disable_telemetry_events')
        embeddings=[n.lineno for n in calls if isinstance(n.func,ast.Name) and n.func.id in ('ImageEmbedding','TextEmbedding')]
        self.assertTrue(all(disable<n for n in embeddings))

    def test_preflight_cannot_publish(self):
        s=(Path(__file__).resolve().parents[1]/'.github/workflows/editorial-photo-preflight.yml').read_text()
        self.assertNotIn('secrets.',s);self.assertNotIn('create_carousel.py',s)
        self.assertIn('if: always()',s)

if __name__=='__main__':unittest.main()
