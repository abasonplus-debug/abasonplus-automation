import unittest
import json, pathlib, tempfile
from unittest.mock import patch
import wordpress_email_prepare as wp
from datetime import datetime, timezone
from scripts.publication_policy import publication_day, trusted_source_url, validate_article_html, validate_social_copy
from scripts.verify_wordpress_publication import verify
from wordpress_email_prepare import prepare

class PublicationPolicyTests(unittest.TestCase):
    def test_business_day_at_bangladesh_midnight_and_dst(self):
        self.assertEqual(str(publication_day(datetime(2026,10,17,21,20,tzinfo=timezone.utc))), '2026-10-17')
        self.assertEqual(str(publication_day(datetime(2026,10,25,23,20,tzinfo=timezone.utc))), '2026-10-26')

    def test_primary_source_hosts_and_spoofed_urls(self):
        for u in ('https://mutation.land.gov.bd/nirdeshika', 'https://bdlaws.minlaw.gov.bd/act', 'https://www.bssnews.net/news/1'):
            self.assertTrue(trusted_source_url(u), u)
        for u in ('https://bdlaws.minlaw.gov.bd.evil.test/x', 'http://land.gov.bd', 'https://user:pass@land.gov.bd', 'https://land.gov.bd:8080/'):
            self.assertFalse(trusted_source_url(u), u)

    def test_html_rejects_hidden_execution_and_email_directives(self):
        validate_article_html('<h2>তথ্য</h2><p><a href="https://land.gov.bd/">উৎস</a></p>')
        for text in ('<p onclick="x()">x</p>', '<a href="javascript:alert(1)">x</a>', '<script>x</script>', '<p>[status private]</p>'):
            with self.assertRaises(ValueError): validate_article_html(text)

    def test_caption_boundaries(self):
        tags='#a #b #c #d #e'
        validate_social_copy(tags, 'description', 'title')
        for args in ((tags+'x'*2200, 'd', 't'), (tags,'d','x'*101), ('#a','d','t')):
            with self.assertRaises(ValueError): validate_social_copy(*args)

    def test_wordpress_requires_exact_identity_and_recent_timestamp(self):
        sent=datetime(2026,10,17,6,20,tzinfo=timezone.utc)
        expected={'post_key':'ap-example-2026-10-17','subject':'পরীক্ষা & যাচাই'}
        post={'ID':1,'slug':expected['post_key'],'title':'পরীক্ষা &amp; যাচাই','status':'publish','date':'2026-10-17T06:20:20+00:00','URL':'https://abasonplus.wordpress.com/2026/10/17/ap-example-2026-10-17/'}
        self.assertTrue(verify(expected,[post],sent)['verified'])
        for change in ({'slug':'another-slug'}, {'title':'different'}, {'date':'2026-10-16T06:20:20Z'}, {'status':'draft'}, {'URL':'https://evil.test/post'}):
            self.assertIsNone(verify(expected,[dict(post,**change)],sent),change)

    def test_missing_daily_editorial_removes_stale_preview_and_holds(self):
        with tempfile.TemporaryDirectory() as directory:
            root=pathlib.Path(directory)
            (root/'content').mkdir(); (root/'output').mkdir()
            (root/'content/researched_wordpress_posts.json').write_text('[]')
            (root/'wordpress_posts.json').write_text('[]')
            stale=root/'output/wordpress_email_preview.json'
            stale.write_text('{"post_key":"old"}')
            with patch.object(wp,'ROOT',root), patch('sys.argv',['prepare','--skip-public-lookup']):
                with self.assertRaisesRegex(RuntimeError,'NO_CHATGPT_DAILY_EDITORIAL'):
                    wp.main()
            self.assertFalse(stale.exists())

    def test_email_body_does_not_accept_injected_posting_instructions(self):
        with self.assertRaises(ValueError):
            prepare({'slug':'ap-safe-slug','title':'তথ্য','content':'<p>'+('তথ্য '*100)+'[delay +2 days]</p>','tags':[]})

    def test_title_body_directive_preserves_bengali_subject_and_blocks_injection(self):
        title='Eco-Build অনুদান: বাংলাদেশের সবুজ নির্মাণে সুযোগ, সীমা ও যাচাই'
        post={'slug':'ap-safe-slug','title':title,'content':'<p>'+('তথ্য '*100)+'</p>','tags':[]}
        result=prepare(post)
        self.assertTrue(result['content'].startswith('[title '+title+']\n'))
        self.assertIn('[title '+title+']',result['html_content'])
        self.assertEqual(result['subject'],title)
        for invalid in ('শিরোনাম [status private]', 'শিরোনাম]'):
            with self.assertRaises(RuntimeError):prepare(dict(post,title=invalid))

if __name__ == '__main__':
    unittest.main()

