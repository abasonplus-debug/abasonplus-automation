# AbasonPlus: প্রতিটি carousel ছবির স্থায়ী নির্দেশ

এই নিয়ম hook এবং প্রতিটি tip-এর আলাদা ছবিতে প্রযোজ্য। বর্তমান style_id: `compact_white_gold_v2`। ১৮ অক্টোবর ২০২৬-এর অনুমোদিত আঁটসাঁট সাদা–হলুদ নমুনা পুরোনো navy/no-outline নিয়মকে প্রতিস্থাপন করেছে।

- ক্যানভাস ঠিক ১০৮০×১৯২০px; ৯:১৬; বিষয়সংশ্লিষ্ট স্বতন্ত্র লাইসেন্সযুক্ত বাস্তব photograph পুরো ক্যানভাসে থাকবে। একই ছবি পুনরায় নয়।
- লেখাই প্রথম অগ্রাধিকার। exact Bengali copy ছবির মাঝখানে ওপর থেকে নিচে একটি গুছানো, compact, center-aligned block-এ থাকবে। বাক্য অনুযায়ী লাইন ভাঙবে; অযথা ফাঁকা অনুচ্ছেদ নয়।
- মূল বাংলা ও Latin fallback font বাস্তবে ১২০px Bold; hook ১৩২px Bold। মাপ কোডে নির্ধারিত ও পরীক্ষিত হবে। যুক্তাক্ষর, কারচিহ্ন ও যতিচিহ্ন ঠিক রাখতে হবে।
- মূল লেখা #FFFFFF; অর্থবহ গুরুত্বপূর্ণ শব্দ #FFD24A। পাতলা #101010 আউটলাইন ৪px এবং খুব কাছে হালকা ছায়া offset ২,৩px। অক্ষরের outline কোনো background box নয়।
- render হওয়া অক্ষর/outline/shadow মেপে একই বাক্যের লাইনে লক্ষ্য ৪px এবং বাক্যের মাঝে ১০px ফাঁক। বাস্তব glyph নিরাপত্তা আগে; কোনো overlap নয়। পুরো block ছবির কেন্দ্রের কাছে থাকবে।
- কোনো text box, panel, বাইরের border, dark overlay বা gradient নয়। লেখা বেশি হলে font ছোট/অক্ষর চেপে সরু/শর্ত বাদ দেওয়া নয়; QA hold করবে। বিষয়বস্তুর প্রয়োজনমতো ৫–১৬ স্লাইড হবে; প্রতিটি ঠিক ৩ সেকেন্ড, সর্বোচ্চ মোট ৫০ সেকেন্ড। এক ছবিতে একাধিক বাক্য অনুমোদিত; জায়গা না ধরলে তথ্য অক্ষুণ্ণ রেখে গবেষণা-পর্যায়ে অতিরিক্ত স্লাইডে ভাগ করবে।
- ছবি: ultra-realistic photography, professional photographer’s final touch, restrained cinematic final director cut। বাস্তব উপকরণ, সঠিক perspective, পরিমিত colour grading, naturally readable composition। সব ছবিকে dusk বা অকারণে dark করার নিয়ম নেই। স্টক ছবিকে নির্দিষ্ট সরকারি প্রকল্পের আসল ছবি বলবে না। ফ্রি workflow লাইসেন্সযুক্ত real stock photo ব্যবহার করে; কোনো paid AI API বা দৈনিক AI image generation নয়।
- আসল গোল AbasonPlus logo প্রস্থ ৭০–৯০px রেখে একেবারে নিচের ডানে, edge থেকে ২৮px দূরে। আসল logo অনুপস্থিত হলে metadata-তে বলবে; invented logo বা বিকল্প wordmark নয়। UI overlay কিছু প্ল্যাটফর্মে একেবারে নিচের logo ঢাকতে পারে—এটি নিম্ন-ডান কোণার নির্বাচিত অবস্থানের সীমা।
- background এবং typography আলাদা ধাপে প্রস্তুত; বাংলা shaping সমর্থিত font দিয়ে কোডে লেখা বসবে। image generator-এর আঁকা লেখা exact font-size verification নয়।
- প্রতিটি ছবিতে font size, glyph coverage, line ink bounds, alignment, spacing, photo clutter/readability এবং logo box পরীক্ষা হবে। লাইসেন্স, source ও subject relevance আগের মতো যাচাই হবে। machine QA-কে human aesthetic approval বলবে না।
- মূল caption/source/hashtag, নিজস্ব MP3, duplicate guards, free-only cost rules এবং প্রতিটি platform-এর publishing permission অপরিবর্তিত। manual preview নিজে থেকে publish নয়।

প্রতিটি স্লাইডের ইনপুট: hook অথবা exact tip text; তার নিজস্ব photographic query; প্রয়োজন হলে অগ্রাধিকার দেওয়া keyword। প্রকৃত আইন/খবর/দাম নিজে থেকে উদ্ভাবন বা অর্থ বদল নয়।

Timing update (owner, 2026-10-20): every image is exactly 3 seconds. This supersedes the former 2-second rule. Keep the 50-second maximum: 5–16 slides, total 15–48 seconds; never make 17 slides (51 seconds). Multiple sentences per image remain allowed. Dense text is not guaranteed readable in three seconds. Historical rendered/published artifacts retain their recorded timing; this change does not authorize re-rendering, resending or approving a different TikTok video.


## Owner superseding update — 22 October 2026

New renders use `narration_v1`, superseding every fixed two/three-second and
15/50-second editorial rule above. Exact hook plus slide texts are narrated in
Bengali; each slide lasts its measured WAV segment plus a short pause. Total
video length is the sum of those segments, not an arbitrary target or truncation.
The operational bound is 5–64 source-checked slides, with existing caption,
font/layout, file-size, provider and free quota limits checked separately.

The default voice is local GPL eSpeak NG (`bn`), offline and subscription-free.
This is synthetic speech, not a promise of natural human narration. The original
assets/abasonplus.mp3 loops quietly underneath (10% gain); no catalog music is
substituted. Narration script and WAV SHA-256, measured segment durations and
padding are independently checked before release and archived with the preview.

Historical media retain their recorded policy. New TikTok exact approval must
match narration hash, timing_mode and slide_durations as well as MP4/caption,
source run/commit, settings and rights; changing voice invalidates an earlier OK.
There is no unattended TikTok upload. No creative is generated merely by a code
validation run. Make's current 5 MB transport remains fail-closed: a longer
video that exceeds it needs an independently reviewed transport solution, never
a blind resend, reduced QA, arbitrary audio cutoff or paid upgrade.
