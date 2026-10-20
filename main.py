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
    prompt = """Create one original anime-aura YouTube Short for AshisAura.
Theme: original anime warriors, glowing eyes, power awakenings,
spiky hair, supernatural aura, lightning, dramatic battles and
cinematic transformations. Do not use copyrighted characters.
Return ONLY valid JSON with keys topic, hook, body, cta, title,
description, tags. The hook must be uppercase and max 7 words.
The body must be 35-55 words and describe a cinematic anime scene.
The title must be max 65 characters. Description: 2 short sentences
plus 3-5 hashtags. Tags: array of 5-10 relevant keywords.
Keep content original and suitable for a general audience."""
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
    import math

    # Each scene gets its own original aura color.
    palettes = [
        ((125, 70, 255), (65, 210, 255)),   # Violet + cyan
        ((255, 45, 105), (255, 145, 50)),   # Crimson + orange
        ((40, 140, 255), (100, 245, 255)),  # Electric blue
        ((180, 55, 255), (255, 60, 170)),   # Purple + pink
        ((255, 190, 35), (255, 90, 30)),    # Golden fire
    ]
    aura, accent = palettes[index % len(palettes)]

    im = Image.new("RGB", (W, H), (4, 5, 18))
    px = im.load()

    # Atmospheric navy background with a colored central glow.
    for y in range(H):
        for x in range(W):
            dx = (x - W * 0.5) / (W * 0.8)
            dy = (y - H * 0.43) / (H * 0.8)
            glow = max(0.0, 1.0 - math.sqrt(dx * dx + dy * dy))
            px[x, y] = (
                min(255, int(4 + aura[0] * glow * 0.20)),
                min(255, int(5 + aura[1] * glow * 0.18)),
                min(255, int(18 + aura[2] * glow * 0.30)),
            )

    d = ImageDraw.Draw(im, "RGBA")
    cx, cy = W // 2, 730

    # Glowing aura rings behind the character.
    for rad in range(410, 100, -22):
        alpha = max(8, 75 - rad // 8)
        d.ellipse(
            (cx-rad, cy-rad, cx+rad, cy+rad),
            outline=(*aura, alpha),
            width=4 if rad < 250 else 2,
        )

    # Small energy particles.
    rng = random.Random(900 + index)
    for _ in range(95):
        x = rng.randint(70, W - 70)
        y = rng.randint(280, 1110)
        r = rng.choice([2, 3, 4, 6])
        col = aura if rng.random() < 0.65 else accent
        d.ellipse((x-r, y-r, x+r, y+r), fill=(*col, rng.randint(90, 230)))

    # Jagged lightning bolts behind the warrior.
    for side in (-1, 1):
        for bolt in range(3):
            x = cx + side * (250 + bolt * 42)
            y = 340 + bolt * 80
            points = [(x, y)]
            for _ in range(6):
                x += side * rng.randint(-35, 35)
                y += rng.randint(45, 90)
                points.append((x, y))
            d.line(points, fill=(*aura, 95), width=13, joint="curve")
            d.line(points, fill=(*accent, 220), width=4, joint="curve")

    # Torso, high collar and shoulders.
    d.polygon(
        [
            (cx-95, 770), (cx+95, 770),
            (cx+155, 875), (cx+245, 1115),
            (cx-245, 1115), (cx-155, 875),
        ],
        fill=(10, 13, 32, 255),
        outline=(*aura, 255),
    )
    d.polygon(
        [(cx-105, 825), (cx, 920), (cx+105, 825),
         (cx+65, 1010), (cx, 1055), (cx-65, 1010)],
        fill=(20, 24, 55, 255),
        outline=(*accent, 220),
    )

    # Neck.
    d.rounded_rectangle(
        (cx-52, 735, cx+52, 850),
        radius=24,
        fill=(112, 73, 79, 255),
        outline=(*aura, 230),
        width=3,
    )

    # Original anime-style face.
    d.ellipse(
        (cx-122, 450, cx+122, 775),
        fill=(224, 174, 151, 255),
        outline=(255, 218, 205, 255),
        width=4,
    )

    # Face shadows and jaw accents.
    d.polygon(
        [(cx, 505), (cx+115, 535), (cx+93, 710),
         (cx+28, 770), (cx, 745)],
        fill=(118, 76, 96, 100),
    )

    # Ears.
    d.ellipse((cx-145, 575, cx-103, 650), fill=(190, 126, 126, 255))
    d.ellipse((cx+103, 575, cx+145, 650), fill=(190, 126, 126, 255))

    # Dramatic spiky hair silhouette.
    hair = (12, 14, 35, 255)
    d.polygon(
        [
            (cx-132, 585), (cx-176, 470), (cx-133, 480),
            (cx-157, 380), (cx-85, 430), (cx-94, 315),
            (cx-28, 405), (cx+8, 285), (cx+42, 405),
            (cx+112, 330), (cx+98, 440), (cx+165, 400),
            (cx+142, 510), (cx+125, 600),
            (cx+88, 510), (cx+35, 485),
            (cx-20, 510), (cx-80, 490),
        ],
        fill=hair,
        outline=(*aura, 255),
    )

    # Hair highlights.
    d.line(
        [(cx-118, 475), (cx-83, 440), (cx-87, 365)],
        fill=(*accent, 230), width=7,
    )
    d.line(
        [(cx+17, 395), (cx+10, 325)],
        fill=(*aura, 245), width=7,
    )
    d.line(
        [(cx+104, 440), (cx+140, 418)],
        fill=(*accent, 220), width=6,
    )

    # Sharp eyebrows.
    d.line(
        [(cx-91, 585), (cx-28, 601)],
        fill=(22, 13, 31, 255), width=13,
    )
    d.line(
        [(cx+28, 601), (cx+91, 585)],
        fill=(22, 13, 31, 255), width=13,
    )

    # Glowing anime eyes with bright pupils and highlights.
    for ex in (cx-60, cx+60):
        d.polygon(
            [(ex-39, 615), (ex, 600), (ex+39, 615),
             (ex+15, 647), (ex-17, 647)],
            fill=(245, 245, 255, 255),
            outline=(*accent, 255),
        )
        d.ellipse(
            (ex-13, 605, ex+13, 642),
            fill=(*aura, 255),
        )
        d.ellipse(
            (ex-5, 610, ex+5, 635),
            fill=(255, 255, 255, 255),
        )
        d.line(
            [(ex-37, 614), (ex, 600), (ex+37, 614)],
            fill=(15, 10, 28, 255), width=5,
        )

    # Nose and determined expression.
    d.line(
        [(cx+4, 630), (cx-4, 672), (cx+12, 676)],
        fill=(105, 63, 78, 210), width=4,
    )
    d.line(
        [(cx-32, 714), (cx, 722), (cx+32, 714)],
        fill=(74, 29, 49, 255), width=5,
    )

    # Aura sparks around the face.
    for side in (-1, 1):
        for j in range(4):
            x = cx + side * (155 + j * 16)
            y = 530 + j * 72
            d.line(
                [(x, y), (x + side * 18, y - 22),
                 (x + side * 8, y + 14)],
                fill=(*accent, 220), width=4,
            )

    # Brand label.
    d.rounded_rectangle(
        (72, 115, 1008, 205),
        radius=35,
        fill=(12, 12, 35, 235),
        outline=(*aura, 230),
        width=3,
    )
    d.text(
        (W//2, 160), "ASHISAURA  •  ANIME AURA",
        font=font(34, True), fill=(240, 238, 255, 255), anchor="mm",
    )

    # Main headline.
    headline = title if index == 0 else [
        "POWER AWAKENING", "UNLEASH YOUR AURA",
        "LIMIT BREAK", "THE FINAL FORM",
    ][min(index - 1, 3)]

    f = font(64, True)
    yy = 1190
    for ln in wrap(d, headline.upper(), f, 900)[:3]:
        d.text(
            (W//2, yy), ln, font=f,
            fill=(255, 255, 255, 255),
            stroke_width=3, stroke_fill=(*aura, 255), anchor="mm",
        )
        yy += 88

    lf = font(36)
    for ln in wrap(d, line, lf, 860)[:3]:
        d.text(
            (W//2, yy+35), ln, font=lf,
            fill=(218, 224, 255, 255), anchor="mm",
        )
        yy += 55

    d.text(
        (W//2, 1770), f"{index+1:02d} / {total:02d}",
        font=font(28, True), fill=(190, 185, 240, 255), anchor="mm",
    )

    im.save(path)


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
