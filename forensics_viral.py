"""EP02 v2：用 Python 鑑識三張爆紅 AI 假圖 / Forensics on famous viral AI fakes
圖片來源 Image sources（Wikimedia Commons，公有領域 public domain）：
  pope.jpg      File:Pope Francis in puffy winter jacket.jpg（Midjourney, 2023-03）
  trump1.jpg    File:Midjourney Photo of Trump's Arrest.jpg（Midjourney，Eliot Higgins 提示 prompted, 2023-03）
  trump2.jpg    File:Trump’s arrest (2).jpg（同上 same series）
真實照片對照 Real-photo reference：
  pentagon_real.jpg  File:The Pentagon January 2008.jpg — David B. Gleason, CC BY-SA 2.0
用法 Usage: python forensics_viral.py [src_dir] [out_dir]
"""
import sys, os, json, numpy as np, cv2
from PIL import Image, ExifTags
SRC = sys.argv[1] if len(sys.argv) > 1 else "src"; OUT = sys.argv[2] if len(sys.argv) > 2 else "out"
os.makedirs(OUT, exist_ok=True)
try:  # 選用：頻道浮水印 optional channel watermark
    sys.path.insert(0, "/workspace/yt-channel/branding"); import watermark as wm; TILE = wm.tile_text
except Exception:
    TILE = lambda im: im
IMGS = {"pope": "pope.jpg", "trump1": "trump1.jpg", "trump2": "trump2.jpg", "real": "pentagon_real.jpg"}

def meta(path):
    """EXIF 與 C2PA 簡易檢查 / quick EXIF + C2PA check (byte scan; use c2patool for real verification)"""
    raw = open(path, "rb").read(); ex = Image.open(path).getexif()
    tags = {ExifTags.TAGS.get(k, str(k)): str(v)[:60] for k, v in ex.items()}
    c2pa = any(m in raw for m in (b"c2pa", b"jumb", b"C2PA"))
    return {"exif_count": len(tags), "make": tags.get("Make"), "model": tags.get("Model"),
            "software": tags.get("Software"), "c2pa_marker": c2pa}

def gray(path, side=1024):
    """讀灰階並置中裁成正方形 / grayscale, centre square crop (no resampling, keeps artifacts)"""
    g = cv2.imread(path, cv2.IMREAD_GRAYSCALE).astype(np.float32); h, w = g.shape; s = min(h, w, side)
    y, x = (h - s) // 2, (w - s) // 2; return g[y:y + s, x:x + s]

def fft_spec(g):
    """高通殘差 → 加窗 FFT → 對數頻譜 / high-pass residual → windowed FFT → log spectrum"""
    res = g - cv2.GaussianBlur(g, (0, 0), 2)
    win = np.outer(np.hanning(g.shape[0]), np.hanning(g.shape[1]))
    spec = np.log1p(np.abs(np.fft.fftshift(np.fft.fft2(res * win))))
    # 週期峰值分數：高頻區最亮 0.05% 與中位數的比 / peak score: top 0.05% vs median in high-freq ring
    n = g.shape[0]; yy, xx = np.mgrid[:n, :n] - n // 2; r = np.hypot(yy, xx)
    ring = spec[(r > n * 0.15) & (np.abs(yy) > 3) & (np.abs(xx) > 3)]
    score = float(np.percentile(ring, 99.95) / np.median(ring))
    v = (spec - np.percentile(spec, 1)) / (np.percentile(spec, 99.9) - np.percentile(spec, 1))
    vis = cv2.applyColorMap(np.clip(v * 255, 0, 255).astype(np.uint8), cv2.COLORMAP_INFERNO)
    return vis, score

def noise(g, block=32):
    """雜訊殘差：減中值濾波；回傳視覺化、平均強度、分格不均勻度 / residual, mean, block CV"""
    r = g - cv2.medianBlur(g.astype(np.uint8), 3).astype(np.float32)
    n = (g.shape[0] // block) * block; b = r[:n, :n].reshape(n // block, block, n // block, block).std(axis=(1, 3))
    vis = cv2.applyColorMap(np.clip(np.abs(r) * 12, 0, 255).astype(np.uint8), cv2.COLORMAP_VIRIDIS)
    return vis, float(np.abs(r).mean()), float(b.std() / (b.mean() + 1e-6))

def save(name, bgr):
    im = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)); TILE(im).save(f"{OUT}/{name}.png")

results = {}
for key, fn in IMGS.items():
    p = f"{SRC}/{fn}"; g = gray(p); fv, fs = fft_spec(g); nv, nm, ncv = noise(g)
    save(f"fft_{key}", fv); save(f"noise_{key}", nv)
    results[key] = {"meta": meta(p), "fft_peak_score": round(fs, 3), "noise_mean": round(nm, 3), "noise_block_cv": round(ncv, 3)}
    print(f"[{key}] FFT 峰值分數 peak score={fs:.3f} | 雜訊平均 noise mean={nm:.3f} | 不均勻度 block CV={ncv:.3f} | "
          f"EXIF={results[key]['meta']['exif_count']} 筆 tags, C2PA={results[key]['meta']['c2pa_marker']}")

# 瑕疵特寫（原圖像素座標，人工標註）/ flaw close-ups (original pixel coords, hand-annotated)
FLAWS = {"pope": [("hand_bottle", 120, 1110, 320, 1323), ("cross_chain", 470, 640, 680, 830), ("glasses", 560, 150, 720, 260)],
         "trump1": [("badge_text", 690, 340, 820, 470), ("extra_hands", 590, 560, 860, 760), ("patch", 140, 140, 240, 240)]}
for key, lst in FLAWS.items():
    im = cv2.imread(f"{SRC}/{IMGS[key]}")
    for name, x0, y0, x1, y1 in lst:
        crop = cv2.resize(im[y0:y1, x0:x1], None, fx=3, fy=3, interpolation=cv2.INTER_NEAREST)  # 不插值放大 no smoothing
        cv2.imwrite(f"{OUT}/crop_{key}_{name}.png", crop)
results["flaw_boxes"] = FLAWS
json.dump(results, open(f"{OUT}/results.json", "w"), indent=1, ensure_ascii=False)
print("完成 Done →", OUT)
