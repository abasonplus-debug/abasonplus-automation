"""Human-written Bengali carousel safeguards for source-grounded automatic reels.

Use one of these *verified generic checklists* when a small local AI outputs
long/unclear slide instructions. These are general due-diligence prompts, not
statements that a specific project is approved, completed, or profitable.
"""
LIBRARY={
 "rail":{
  "hook":"মেট্রোরেলের পাশে জমি? আগে যাচাই করুন!",
  "cover_query":"metro train station construction city",
  "tips":[
   ("স্টেশনের আসল অবস্থান যাচাই করুন","metro railway station outdoor"),
   ("জমি অধিগ্রহণের তথ্য জেনে নিন","surveying land construction"),
   ("রাস্তা ও পানি নিষ্কাশন পরীক্ষা করুন","city street drainage road"),
   ("দামের প্রমাণ দেখে সিদ্ধান্ত নিন","real estate agreement office") ]},
 "industry":{
  "hook":"নতুন শিল্পাঞ্চলে জমি? ঝুঁকিও দেখুন!",
  "cover_query":"industrial zone road construction",
  "tips":[
   ("প্রকল্পের অনুমোদন ও অগ্রগতি দেখুন","industrial factory construction"),
   ("জমির ব্যবহার বিধি যাচাই করুন","land document property consultation"),
   ("রাস্তা ও পরিবেশের অবস্থা দেখুন","industrial access road"),
   ("লাভ নিশ্চিত ধরে নেবেন না","real estate agent contract meeting") ]},
 "building":{
  "hook":"বাড়ির নিরাপত্তা? এই তথ্যগুলো জানুন!",
  "cover_query":"professional structural engineer construction site",
  "tips":[
   ("অনুমোদিত নকশা যাচাই করুন","architectural building blueprint"),
   ("মাটির পরীক্ষার নথি দেখুন","soil engineer construction site"),
   ("উপকরণের মান যাচাই করুন","construction materials concrete lab"),
   ("প্রকৌশলীর লিখিত মত নিন","structural engineer site inspection") ]},
 "material":{
  "hook":"নির্মাণসামগ্রী কিনবেন? মান দেখুন!",
  "cover_query":"cement steel construction materials warehouse",
  "tips":[
   ("নকশার নির্ধারিত গ্রেড মিলান","structural engineer materials"),
   ("ব্যাচ ও চালান যাচাই করুন","construction invoices office desk"),
   ("মান পরীক্ষার রিপোর্ট দেখুন","concrete quality control laboratory"),
   ("শুধু দাম নয় মোট খরচ তুলুন","contractor construction estimate") ]},
 "general":{
  "hook":"নতুন সরকারি প্রকল্প? আগে যাচাই করুন!",
  "cover_query":"government infrastructure construction road",
  "tips":[
   ("সরকারি উৎস থেকে অবস্থা জানুন","government infrastructure site"),
   ("জমির অধিকার ও নথি যাচাই করুন","real estate ownership documents"),
   ("রাস্তা ও স্থানীয় চাহিদা দেখুন","new paved rural access road"),
   ("সুযোগের সঙ্গে ঝুঁকিও হিসাব করুন","property developer client meeting") ]}
}
def select(source_title):
    t=source_title.lower()
    if any(s in t for s in ("metro","rail","mrt","station","মেট্রো")):
        return "rail",LIBRARY["rail"]
    if any(s in t for s in ("economic zone","industrial","free trade zone","factory","port","solar","power plant","অর্থনৈতিক")):
        return "industry",LIBRARY["industry"]
    if any(s in t for s in ("earthquake","structural","building safety","soil test","ভূমিকম্প")):
        return "building",LIBRARY["building"]
    if any(s in t for s in ("cement","steel","brick","construction material","রড","সিমেন্ট")):
        return "material",LIBRARY["material"]
    return "general",LIBRARY["general"]

def safeguard_slide_text(generated, source_title):
    category,base=select(source_title)
    # A small AI can supply Bengali text that is fluent yet nonsensical.
    # Use reviewed due-diligence wording instead for automated video.
    video={
      "hook":base["hook"],
      "cover_query":base["cover_query"],
      "tips":[{"text":t,"query":q} for t,q in base["tips"]]
    }
    return category,video
