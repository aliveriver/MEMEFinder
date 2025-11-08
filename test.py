# test.py  —— 最小可复现且鲁棒的单图测试
import json
from pathlib import Path

import paddle
from PIL import Image, ImageOps
from paddleocr import PaddleOCR

IMG_PATH = r"D:\MEMEFinder\imgs\F4AE5C16BEAC75BD2B46D1A99A5ECE07.jpg"

def pad_border(img: Image.Image, ratio: float = 0.03, color=(0, 0, 0)):
    w, h = img.size
    pad = max(2, int(round(max(w, h) * ratio)))
    return ImageOps.expand(img, border=(pad, pad, pad, pad), fill=color), pad

def normalize_result(res):
    """
    将多种可能的返回格式统一成：
    [{"box": [[x,y],...], "text": "xxx", "score": 0.xx}, ...]
    """
    out = []

    if res is None:
        return out

    # 情况A：某些版本 predict 返回 [lines]，而 lines 是一个 list
    if isinstance(res, (list, tuple)):
        # 如果是 [lines] 这种外层再包一层
        if len(res) == 1 and isinstance(res[0], (list, tuple)):
            lines = res[0]
        else:
            lines = res
        for line in lines:
            try:
                # 常见： [box, (text, score)]
                if isinstance(line, (list, tuple)) and len(line) >= 2:
                    box = line[0]
                    rec = line[1]
                    if hasattr(box, "tolist"):
                        box = box.tolist()
                    # rec 可能是 (text, score) / {"text": "..."} / "text"
                    if isinstance(rec, (list, tuple)):
                        text = rec[0]
                        score = float(rec[1]) if len(rec) > 1 else 0.0
                    elif isinstance(rec, dict):
                        text = rec.get("text", "")
                        score = float(rec.get("confidence", rec.get("score", 0.0)) or 0.0)
                    else:
                        text = str(rec)
                        score = 0.0
                    out.append({"box": box, "text": text, "score": score})
                # 另一种可能：直接是 dict
                elif isinstance(line, dict):
                    text = line.get("text", "")
                    score = float(line.get("confidence", line.get("score", 0.0)) or 0.0)
                    box = line.get("box", line.get("poly", []))
                    out.append({"box": box, "text": text, "score": score})
            except Exception:
                continue
        return out

    # 情况B：字典类型（极少数封装）
    if isinstance(res, dict):
        # 常见键尝试
        cand = res.get("result") or res.get("data") or res.get("res") or []
        if isinstance(cand, (list, tuple)):
            return normalize_result(cand)
        # 有的直接就放在 dict 中不可迭代，放弃
        return out

    # 其他类型
    return out

def main():
    paddle.set_device("cpu")  # 避免你本机 cuDNN 版本不匹配的警告影响结果

    # 1) 读图+加黑边（解决贴边漏检）
    img = Image.open(IMG_PATH).convert("RGB")
    padded, pad = pad_border(img, ratio=0.03, color=(0, 0, 0))
    tmp_path = Path(IMG_PATH).with_suffix(".pad.jpg")
    padded.save(tmp_path)

    # 2) 初始化 OCR（放宽检测阈值、提高分辨率）
    ocr = PaddleOCR(
        lang="ch",
        use_textline_orientation=True,
        text_det_limit_side_len=1920,
        text_det_limit_type="max",
        text_det_thresh=0.2,
        text_det_box_thresh=0.3,
        text_det_unclip_ratio=2.6,
    )

    # 3) 调用 predict，必要时回退到 ocr()
    try:
        res = ocr.predict(str(tmp_path))
    except TypeError:
        tmp = ocr.predict([str(tmp_path)])
        res = tmp[0] if isinstance(tmp, (list, tuple)) and len(tmp) else tmp
    except Exception:
        res = None

    if not res:
        try:
            res = ocr.ocr(str(tmp_path))
        except Exception:
            res = None

    items = normalize_result(res)

    # 4) 去掉加边的坐标偏移，打印
    def _shift_back(box):
        try:
            if hasattr(box, "tolist"):
                box = box.tolist()
            return [[int(p[0]) - pad, int(p[1]) - pad] for p in box]
        except Exception:
            return box

    for it in items:
        it["box"] = _shift_back(it.get("box", []))

    # 输出文本列表
    texts = [it["text"] for it in items if it.get("text")]
    print(json.dumps({"texts": texts, "n": len(texts)}, ensure_ascii=False, indent=2))

    # 如需看框与分数，解除下面注释
    # print(json.dumps(items, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
