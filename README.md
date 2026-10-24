# EP02：AI 生成圖怎麼抓？用 Python 看穿 4 個破綻

[English below](#english)

**照妖鏡實驗室 PixelProbe** YouTube 影片〈AI 生成圖怎麼抓？〉的完整程式碼。影片只展示關鍵幾行，這裡是可直接執行的完整版本。

## 內容
程式**自行生成**兩張模擬圖：「相機風格」（全解析度 + 散粒雜訊 + 類 PRNU 感光圖樣）與「AI 風格」（低解析度兩次最近鄰放大 + 棋盤格痕跡），接著分析：

| 方法 | 輸出 |
|---|---|
| 頻譜 FFT（高通殘差 → 對數頻譜，週期峰值比） | `01_fft_*.png`、`fft_peak_ratio` |
| 雜訊殘差（減中值濾波，32×32 分格標準差） | `02_noise_*.png`、`noise_mean` |
| 相鄰像素相同比例 | `equal_neighbour_frac` |
| EXIF／C2PA 簡易檢查 | `meta_ai` |

數值存在 `out/results.json`。參考結果：峰值比 相機 1.03 / AI 1.87；雜訊 相機 4.8 / AI 0.8。

## 執行
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python forensics_ai_demo.py
```

## 重要限制
- 這是**模擬**，真實 AI 模型的痕跡更細微，且會被壓縮、縮放、加雜訊抹除。
- C2PA 檢查只搜尋位元組，正式驗證請用 [c2patool](https://github.com/contentauth/c2patool) 或 contentcredentials.org。
- AI 偵測器（含預訓練模型）準確率不穩定。**沒有單一方法能證明圖片由 AI 生成**，請交叉比對並追查來源。

## 授權
MIT License，見 `LICENSE`。

---

<a id="english"></a>
# EP02: How to Spot AI Images with Python (4 clues)

Full code for the **PixelProbe** YouTube video. The video shows only key lines; this is the complete runnable version.

## What it does
The script **generates** two simulated images, a "camera-like" one (full resolution + shot noise + PRNU-like sensor pattern) and an "AI-like" one (low-res upscaled twice with nearest-neighbour + checkerboard artifact), then analyses:

| Method | Output |
|---|---|
| FFT spectrum (high-pass residual → log spectrum, periodic peak ratio) | `01_fft_*.png`, `fft_peak_ratio` |
| Noise residual (minus median filter, std per 32×32 block) | `02_noise_*.png`, `noise_mean` |
| Identical neighbour-pixel fraction | `equal_neighbour_frac` |
| EXIF / C2PA quick check | `meta_ai` |

Numbers go to `out/results.json`. Reference: peak ratio camera 1.03 / AI 1.87; noise camera 4.8 / AI 0.8.

## Run
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python forensics_ai_demo.py
```

## Limitations
- This is a **simulation**; real generator traces are subtler and can be erased by compression, resizing or added noise.
- The C2PA check is a byte search only; use [c2patool](https://github.com/contentauth/c2patool) or contentcredentials.org for real verification.
- AI detectors (including pretrained models) are unreliable. **No single method proves an image is AI-generated**; cross-check and trace the source.

## License
MIT, see `LICENSE`.
