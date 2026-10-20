import os, json, random, subprocess, textwrap, datetime, re, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import requests
import edge_tts
import asyncio
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

ROOT = Path(__file__).parent
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)
W, H = 1080, 1920
VOICE = os.getenv("TTS_VOICE", "en-US-GuyNeural")
PUBLISH_HOUR_IST = int(os.getenv("PUBLISH_HOUR_IST", "19"))
PUBLISH_MINUTE_IST = int(os.getenv("PUBLISH_MINUTE_IST", "0"))

IDEAS = [
    {
        "topic": "Awaken Your Hidden Power",
        "hook": "YOUR TRUE POWER IS STILL SLEEPING",
        "body": "The strongest warriors are not born awakened. They train in silence, face their shadows, and rise after every defeat. Your next transformation begins when you refuse to give up.",
        "cta": "FOLLOW ASHISAURA FOR MORE AURA"
    },
    {
        "topic": "The Coldest Anime Aura",
        "hook": "ONE LOOK. UNLIMITED POWER.",
        "body": "The battlefield goes silent. His eyes begin to glow as violet energy tears through the darkness. He takes one step forward, and everyone realizes the real battle has just begun.",
        "cta": "COMMENT YOUR AURA COLOR"
    },
    {
        "topic": "Limit Break Transformation",
        "hook": "THIS IS HIS FINAL FORM",
        "body": "Blue flames rise around the warrior. Lightning cracks across his awakened eyes. Every limit he once believed in disappears as a new force erupts from within.",
        "cta": "FOLLOW FOR THE NEXT AWAKENING"
    },
    {
        "topic": "Shadow Warrior Awakening",
        "hook": "NEVER UNDERESTIMATE THE QUIET ONE",
        "body": "He stands alone beneath a crimson sky. Dark energy coils around his body, his eyes flash red, and the ground trembles. The shadow warrior has finally awakened.",
        "cta": "WHICH AURA WOULD YOU CHOOSE"
    },
    {
        "topic": "The Power Behind Glowing Eyes",
        "hook": "WHEN HIS EYES CHANGE, RUN",
        "body": "A golden light ignites inside his eyes. Energy spirals into the sky as his hair lifts in the storm. This is not anger. This is power finally unleashed.",
        "cta": "FOLLOW ASHISAURA FOR MORE"
    },
    {
        "topic": "The Last Warrior Standing",
        "hook": "HE REFUSED TO FALL",
        "body": "Broken armor. Burning skies. One warrior still stands. His electric blue aura returns brighter than before, proving that the final strike belongs to the one who keeps fighting.",
        "cta": "SAVE THIS AURA MOMENT"
    }
]


def gemini_idea():
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        return None
    # Optional: Gemini API key from Google AI Studio. If unavailable/quota-limited, use built-in ideas.
    prompt = """Create one original, safe-for-work 25-35 second YouTube Short for AshisAura, a motivational anime-aura mindset channel. Do not use copyrighted characters, quotes, lyrics, or claim a quote is from a real person. Return ONLY valid JSON with keys topic, hook (max 7 words, uppercase), body (35-55 words), cta (max 8 words), title (max 65 chars), description (2 short sentences plus 3-5 hashtags), tags (array of 5-10 relevant keyword strings). Avoid repetitive clickbait."""
    try:
        r = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
            params={"key": key},
            json={"contents":[{"parts":[{"text":prompt}]}],
                  "generationConfig":{"responseMimeType":"application/json","temperature":0.9}},
            timeout=45
        )
        r.raise_for_status()
        data = r.json()
        raw = data["candidates"][0]["content"]["parts"][0]["text"]
        obj = json.loads(raw)
        required = {"topic","hook","body","cta"}
        if not required.issubset(obj) or len(str(obj["body"]).split()) < 20:
            return None
        return obj
    except Exception as e:
        print(f"Gemini unavailable; using fallback idea. Details: {e}", flush=True)
        return None

def choose_idea():
    generated = gemini_idea()
    if generated:
        return generated
    # Stable daily rotation so a retry on the same UTC date uses the same topic.
    day = datetime.datetime.now(datetime.timezone.utc).date().toordinal()
    return IDEAS[day % len(IDEAS)]

def font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            return ImageFont.truetype(p, size=size)
    return ImageFont.load_default()

def wrap(draw, text, fnt, max_width):
    words = str(text).split()
    lines, cur = [], ""
    for word in words:
        test = f"{cur} {word}".strip()
        if draw.textbbox((0,0), test, font=fnt)[2] <= max_width:
            cur = test
        else:
            if cur: lines.append(cur)
            cur = word
    if cur: lines.append(cur)
    return lines

def make_scene(path, title, line, index, total):
    im = Image.new("RGB", (W,H), (5, 7, 22))
    px = im.load()
    # Deep navy/purple gradient with a central aura glow.
    for y in range(H):
        for x in range(W):
            dx, dy = (x-W*0.5)/(W*0.75), (y-H*0.45)/(H*0.75)
            glow = max(0, 1-(dx*dx+dy*dy)**0.5)
            px[x,y] = (int(5+18*glow), int(7+8*glow), int(22+65*glow))
    d = ImageDraw.Draw(im, "RGBA")
    cx, cy = W//2, H//2-70
    for rad in range(500, 70, -24):
        alpha = max(3, 22-int(rad/30))
        d.ellipse((cx-rad,cy-rad,cx+rad,cy+rad), outline=(105,95,255,alpha), width=5)
    # Original abstract silhouette, not a known character.
    d.ellipse((cx-95, cy-290, cx+95, cy-100), fill=(10,12,30,255), outline=(170,150,255,220), width=7)
    d.polygon([(cx-220,cy+250),(cx-130,cy-110),(cx+130,cy-110),(cx+220,cy+250)], fill=(10,12,30,255), outline=(135,125,255,230))
    d.line((cx-150,cy+10,cx,cy+120,cx+150,cy+10), fill=(140,225,255,200), width=8)
    # Top label and scene text.
    d.rounded_rectangle((72,115,1008,205), radius=35, fill=(22,20,55,220), outline=(140,130,255,180), width=3)
    d.text((W//2,160), "ASHISAURA  •  MINDSET", font=font(34,True), fill=(225,225,255), anchor="mm")
    headline = title if index == 0 else ["REMEMBER THIS","STAY FOCUSED","KEEP BUILDING","YOUR NEXT MOVE"][min(index-1,3)]
    f = font(66, True)
    lines = wrap(d, headline.upper(), f, 900)
    yy = 1190
    for ln in lines[:3]:
        d.text((W//2,yy), ln, font=f, fill=(255,255,255), stroke_width=2, stroke_fill=(18,12,60), anchor="mm")
        yy += 88
    lf = font(38)
    for ln in wrap(d, line, lf, 860)[:3]:
        d.text((W//2,yy+35), ln, font=lf, fill=(205,218,255), anchor="mm")
        yy += 55
    d.text((W//2,1770), f"{index+1:02d} / {total:02d}", font=font(28,True), fill=(160,160,220), anchor="mm")
    im.save(path, quality=92)

async def make_voice(text, outpath):
    communicate = edge_tts.Communicate(text, VOICE, rate="+4%", volume="+0%")
    await communicate.save(str(outpath))

def run(cmd):
    subprocess.run(cmd, check=True)

def render_video(idea):
    voice_text = f"{idea['hook']}. {idea['body']} {idea['cta']}."
    audio = OUT / "voice.mp3"
    asyncio.run(make_voice(voice_text, audio))
    # Read narration length and divide into five scenes; ffmpeg is installed on GitHub runner.
    probe = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(audio)],
                           capture_output=True, text=True, check=True)
    duration = max(18.0, float(probe.stdout.strip()) + 1.0)
    scenes = [
        (idea["hook"], idea["body"][:110]),
        ("DISCIPLINE", idea["body"][:100]),
        ("FOCUS", idea["body"][100:220] or idea["body"]),
        ("KEEP GOING", idea["body"][-100:]),
        (idea["cta"], "Follow AshisAura for original mindset Shorts."),
    ]
    concat = OUT / "scenes.txt"
    lines = []
    per = duration / len(scenes)
    for i,(head,line) in enumerate(scenes):
        p = OUT / f"scene_{i}.png"
        make_scene(p, head, line, i, len(scenes))
        lines += [f"file '{p.as_posix()}'", f"duration {per:.3f}"]
    lines.append(f"file '{(OUT / 'scene_4.png').as_posix()}'")
    concat.write_text("\n".join(lines), encoding="utf-8")
    mp4 = OUT / "ashisaura_short.mp4"
    run(["ffmpeg","-y","-hide_banner","-loglevel","error","-f","concat","-safe","0","-i",str(concat),
         "-i",str(audio),"-vf","scale=1080:1920,format=yuv420p","-r","30","-c:v","libx264","-preset","veryfast",
         "-crf","25","-c:a","aac","-b:a","128k","-shortest","-movflags","+faststart",str(mp4)])
    return mp4

def seo(idea):
    title = str(idea.get("title") or f"{idea['topic']} ⚡ | AshisAura #Shorts")[:95]
    desc = idea.get("description") or (
        f"{idea['body']}\n\nFollow AshisAura for original mindset and aura edits.\n"
        "#Shorts #Mindset #Discipline #Motivation #AshisAura"
    )
    tags = idea.get("tags") or ["AshisAura","mindset","discipline","motivation","self improvement","aura edit","shorts"]
    return title, desc[:4900], [str(t)[:100] for t in tags[:20]]

def credentials():
    token = ROOT / "token.json"
    client = ROOT / "client_secret.json"
    if not token.exists() or not client.exists():
        raise SystemExit("Missing token.json/client_secret.json. Follow README OAuth setup and add GitHub secrets.")
    creds = Credentials.from_authorized_user_file(str(token), ["https://www.googleapis.com/auth/youtube.upload"])
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token.write_text(creds.to_json(), encoding="utf-8")
    return creds

def next_publish_at():
    # Schedule for today's target time in India, or tomorrow if the run is too late.
    from zoneinfo import ZoneInfo
    now = datetime.datetime.now(ZoneInfo("Asia/Kolkata"))
    target = now.replace(hour=PUBLISH_HOUR_IST, minute=PUBLISH_MINUTE_IST, second=0, microsecond=0)
    if target <= now + datetime.timedelta(minutes=20):
        target += datetime.timedelta(days=1)
    return target.astimezone(datetime.timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z")

def upload(video, idea):
    creds = credentials()
    youtube = build("youtube","v3",credentials=creds)
    title, description, tags = seo(idea)
    body = {
        "snippet":{"title":title,"description":description,"tags":tags,"categoryId":"22","defaultLanguage":"en"},
        "status":{"privacyStatus":"private","publishAt":next_publish_at(),"selfDeclaredMadeForKids":False}
    }
    request = youtube.videos().insert(part="snippet,status", body=body,
        media_body=MediaFileUpload(str(video), mimetype="video/mp4", resumable=True, chunksize=8*1024*1024))
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Upload progress: {int(status.progress()*100)}%", flush=True)
    print("Upload complete. Video ID:", response.get("id"))
    print("Scheduled publish time (UTC):", body["status"]["publishAt"])
    print("Title:", title)
    return response.get("id")

def main():
    idea = choose_idea()
    print("Today's topic:", idea["topic"], flush=True)
    (OUT / "seo.json").write_text(json.dumps(idea, ensure_ascii=False, indent=2), encoding="utf-8")
    video = render_video(idea)
    if os.getenv("DRY_RUN","").lower() == "true":
        print("DRY_RUN=true; video rendered but not uploaded:", video)
        return
    upload(video, idea)

if __name__ == "__main__":
    main()
