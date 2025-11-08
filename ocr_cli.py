#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PaddleOCR 3.3.x 命令行工具（画布外扩 + 检测参数调优，精简版）
- 单图 / 批量目录识别
- 四周加黑边（--pad-ratio），识别后坐标回退到原图系
- 可视化（优先 draw_ocr，失败回退 OpenCV）
- 保存 JSON / JSONL / CSV
- --debug 保存 Paddle 原始返回到 out/debug/*.paddle.raw.json
"""

import os
import sys
import json
import csv
import argparse
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
from PIL import Image
import cv2
import paddle

# --- PaddleOCR ---
from paddleocr import PaddleOCR
try:
    from paddleocr import draw_ocr  # 优先
except Exception:
    try:
        from paddleocr.tools.infer.utility import draw_ocr
    except Exception:
        draw_ocr = None

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"}


# ---------------- 基础工具 ----------------

def is_image_file(p: Path) -> bool:
    return p.is_file() and p.suffix.lower() in IMG_EXTS

def collect_images(input_path: Path) -> List[Path]:
    if input_path.is_file() and is_image_file(input_path):
        return [input_path]
    if input_path.is_dir():
        return [p for p in sorted(input_path.rglob("*")) if is_image_file(p)]
    return []

def _json_dumpable(obj):
    try:
        json.dumps(obj)
        return obj
    except Exception:
        if hasattr(obj, "tolist"):
            try:
                return obj.tolist()
            except Exception:
                pass
        if isinstance(obj, (list, tuple)):
            return [_json_dumpable(x) for x in obj]
        if isinstance(obj, dict):
            return {k: _json_dumpable(v) for k, v in obj.items()}
        return repr(obj)

def _save_raw_debug(out_dir: Path, img_path: Path, res: Any):
    dbg = out_dir / "debug"
    dbg.mkdir(parents=True, exist_ok=True)
    with open(dbg / f"{img_path.stem}.paddle.raw.json", "w", encoding="utf-8") as f:
        json.dump(_json_dumpable(res), f, ensure_ascii=False, indent=2)


# ---------------- OCR 统一解析 ----------------

def ocr_single(ocr: PaddleOCR, img_path: Path, debug_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    统一输出：
    { "image": "...", "items": [{"box":[[x,y]x4], "text":"...", "score":0.xx}, ...] }
    兼容 predict/ocr、新旧返回结构。
    """
    res = None
    try:
        try:
            res = ocr.predict(str(img_path))
        except TypeError:
            tmp = ocr.predict([str(img_path)])
            res = tmp[0] if isinstance(tmp, (list, tuple)) and len(tmp) == 1 else tmp
    except Exception:
        res = None

    if not res:
        try:
            res = ocr.ocr(str(img_path))
        except Exception:
            res = None

    if debug_dir is not None:
        _save_raw_debug(debug_dir, img_path, res)

    items: List[Dict[str, Any]] = []
    if not res:
        return {"image": str(img_path), "items": items}

    def _tolist(x):
        try:
            return x.tolist() if hasattr(x, "tolist") else x
        except Exception:
            return x

    def _find_inner_res(d):
        # 递归查找包含 rec_texts + (rec_polys|dt_polys) 的层
        if isinstance(d, dict):
            if "res" in d and isinstance(d["res"], dict):
                v = d["res"]; ks = v.keys()
                if ("rec_texts" in ks) and (("rec_polys" in ks) or ("dt_polys" in ks)):
                    return v
            ks = d.keys()
            if ("rec_texts" in ks) and (("rec_polys" in ks) or ("dt_polys" in ks)):
                return d
            for v in d.values():
                inner = _find_inner_res(v)
                if inner is not None:
                    return inner
        elif isinstance(d, (list, tuple)):
            for v in d:
                inner = _find_inner_res(v)
                if inner is not None:
                    return inner
        return None

    inner = _find_inner_res(res)
    if inner is not None:
        texts  = list(inner.get("rec_texts") or [])
        scores = list(inner.get("rec_scores") or [])
        polys  = _tolist(inner.get("rec_polys") or inner.get("dt_polys"))
        n = len(texts)
        for i in range(n):
            text  = str(texts[i])
            score = float(scores[i]) if i < len(scores) else 0.0
            if polys is not None and i < len(polys):
                box = _tolist(polys[i])
                if isinstance(box, (list, tuple)) and len(box) == 4 and all(
                    isinstance(p, (list, tuple)) and len(p) == 2 for p in box
                ):
                    items.append({"box": box, "text": text, "score": score})
        return {"image": str(img_path), "items": items}

    # 旧风格
    def _num(x): return isinstance(x, (int, float, np.integer, np.floating))
    def _pt(p):  return isinstance(p, (list, tuple, np.ndarray)) and len(p) == 2 and _num(p[0]) and _num(p[1])

    def _box(b):
        if hasattr(b, "tolist"):
            try: b = b.tolist()
            except Exception: return None
        return b if (isinstance(b, (list, tuple)) and len(b) == 4 and all(_pt(p) for p in b)) else None

    def _ts(v):
        return (isinstance(v, (list, tuple)) and len(v) >= 2 and isinstance(v[0], str) and _num(v[1]))

    if isinstance(res, (list, tuple)) and len(res) > 0:
        first = res[0]
        if isinstance(first, (list, tuple)) and first and isinstance(first[0], (list, tuple)):
            for line in first:
                if not (isinstance(line, (list, tuple)) and len(line) >= 2): continue
                b = _box(line[0]); ts = line[1]
                if b is not None and _ts(ts):
                    items.append({"box": b, "text": ts[0], "score": float(ts[1])})
            if items: return {"image": str(img_path), "items": items}

        ok = False
        for line in res:
            if not (isinstance(line, (list, tuple)) and len(line) >= 2): continue
            b = _box(line[0]); ts = line[1]
            if b is not None and _ts(ts):
                items.append({"box": b, "text": ts[0], "score": float(ts[1])}); ok = True
        if ok: return {"image": str(img_path), "items": items}

    if (isinstance(res, (list, tuple)) and len(res) == 2
            and isinstance(res[0], (list, tuple)) and isinstance(res[1], (list, tuple))):
        det_boxes, recs = res[0], res[1]
        n = min(len(det_boxes), len(recs))
        for i in range(n):
            b = _box(det_boxes[i]); ts = recs[i]
            if b is not None and _ts(ts):
                items.append({"box": b, "text": ts[0], "score": float(ts[1])})
        if items: return {"image": str(img_path), "items": items}

    seq = res if isinstance(res, (list, tuple)) else [res]
    took = False
    for d in seq:
        if not isinstance(d, dict): continue
        b = _box(d.get("box") or d.get("bbox") or d.get("points") or d.get("poly") or d.get("det"))
        ts = d.get("rec")
        text = d.get("text") or d.get("transcription") or d.get("label")
        score = d.get("score") or d.get("confidence") or d.get("prob")
        if ts and _ts(ts):
            text, score = ts[0], ts[1]
        if b is not None and isinstance(text, str):
            items.append({"box": b, "text": text, "score": float(score or 0.0)}); took = True
    if took: return {"image": str(img_path), "items": items}

    return {"image": str(img_path), "items": []}


# ---------------- 画布外扩 + 坐标回退 ----------------

def _parse_color(s: str):
    s = (s or "").strip()
    if s.startswith("#") and len(s) in (4, 7):
        if len(s) == 4:
            r = int(s[1]*2, 16); g = int(s[2]*2, 16); b = int(s[3]*2, 16)
        else:
            r = int(s[1:3], 16); g = int(s[3:5], 16); b = int(s[5:7], 16)
        return (r, g, b)
    if "," in s:
        try:
            r, g, b = [int(x) for x in s.split(",")]
            return (r, g, b)
        except Exception:
            pass
    return (0, 0, 0)

def _make_padded_tmp(img_path: Path, pad_ratio: float, pad_color=(0,0,0)):
    """
    返回：td(临时目录或 None), padded_path(供 OCR 的路径), (px, py), (w, h)
    """
    img = Image.open(img_path).convert("RGB")
    w, h = img.size
    if pad_ratio <= 0:
        return None, img_path, (0, 0), (w, h)

    px = max(1, int(round(w * pad_ratio)))
    py = max(1, int(round(h * pad_ratio)))
    canvas = Image.new("RGB", (w + 2*px, h + 2*py), pad_color)
    canvas.paste(img, (px, py))

    td = tempfile.TemporaryDirectory()
    outp = Path(td.name) / f"{img_path.stem}.padded.png"
    canvas.save(outp)
    return td, outp, (px, py), (w, h)

def _shift_items_to_original(items: List[Dict[str,Any]], dx: int, dy: int, orig_wh=None):
    W, H = orig_wh if orig_wh else (None, None)
    shifted = []
    for it in items:
        box = [[p[0]-dx, p[1]-dy] for p in it["box"]]
        if W is not None and H is not None:
            box = [[max(0, min(W-1, x)), max(0, min(H-1, y))] for x, y in box]
        shifted.append({**it, "box": box})
    return shifted


# ---------------- 可视化 & 保存 ----------------

def visualize(img_path: Path, result: Dict[str, Any], save_path: Path, font_path: Optional[str] = None):
    image = Image.open(img_path).convert("RGB")
    boxes = [it["box"] for it in result.get("items", [])]
    txts = [it["text"] for it in result.get("items", [])]
    scores = [it["score"] for it in result.get("items", [])]

    save_path.parent.mkdir(parents=True, exist_ok=True)
    if not boxes:
        image.save(save_path); return

    if draw_ocr is not None:
        try:
            vis_arr = draw_ocr(image, boxes, txts, scores, font_path=font_path)
            Image.fromarray(vis_arr).save(save_path)
            return
        except Exception:
            pass

    cv_img = np.array(image).copy()
    def _pt(pt): return (int(round(pt[0])), int(round(pt[1])))
    for box, txt in zip(boxes, txts):
        try:
            pts = np.array([_pt(p) for p in box], dtype=np.int32)
            cv2.polylines(cv_img, [pts], True, (0, 255, 0), 2, cv2.LINE_AA)
            x, y = pts[0]; w = 10 * min(len(txt), 30)
            cv2.rectangle(cv_img, (x, y - 22), (x + w, y), (0, 255, 0), -1)
            cv2.putText(cv_img, txt[:30], (x + 2, y - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
        except Exception:
            continue
    Image.fromarray(cv_img).save(save_path)

def save_json(results: List[Dict[str, Any]], save_path: Path):
    save_path.parent.mkdir(parents=True, exist_ok=True)
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

def save_jsonl(results: List[Dict[str, Any]], save_path: Path):
    save_path.parent.mkdir(parents=True, exist_ok=True)
    with open(save_path, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def save_csv(results: List[Dict[str, Any]], save_path: Path):
    save_path.parent.mkdir(parents=True, exist_ok=True)
    with open(save_path, "w", encoding="utf-8", newline=""):
        pass
    with open(save_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["image", "text", "score", "box"])
        for r in results:
            img = r.get("image", "")
            for it in r.get("items", []):
                writer.writerow([img, it["text"], it["score"], json.dumps(it["box"], ensure_ascii=False)])


# ---------------- 参数 & 主逻辑 ----------------

def parse_args():
    ap = argparse.ArgumentParser(description="PaddleOCR（画布外扩 + 调参，精简版）")
    ap.add_argument("--input", required=True, help="输入图片或目录路径")
    ap.add_argument("--out", default="./ocr_out", help="输出目录")
    ap.add_argument("--lang", default="ch", help="语言：ch / en / ja / ko / fr / de / ...")
    ap.add_argument("--gpu", action="store_true", help="使用 GPU（需 paddlepaddle-gpu）")
    ap.add_argument("--angle-cls", dest="angle_cls", action="store_true", default=True,
                    help="启用文本行方向判断（默认开）")
    ap.add_argument("--no-angle-cls", dest="angle_cls", action="store_false",
                    help="关闭文本行方向判断")
    ap.add_argument("--vis", action="store_true", help="保存可视化图片")
    ap.add_argument("--save-json", action="store_true", help="保存 results.json")
    ap.add_argument("--save-jsonl", action="store_true", help="保存 results.jsonl")
    ap.add_argument("--save-csv", action="store_true", help="保存 results.csv")
    ap.add_argument("--limit", type=int, default=0, help="仅处理前 N 张（0 表示不限制）")
    ap.add_argument("--font-path", type=str, default=None, help="可视化中文字体路径，如 C:/Windows/Fonts/msyh.ttc")
    ap.add_argument("--debug", action="store_true", help="保存原始返回到 out/debug/*.paddle.raw.json")

    # 画布外扩
    ap.add_argument("--pad-ratio", type=float, default=0.10,
                    help="四周添加黑边比例（相对于原图宽/高），默认 0.10；<=0 不加边")
    ap.add_argument("--pad-color", type=str, default="#000000",
                    help="填充颜色，HEX 或 'r,g,b'，默认黑色")

    # 检测输入尺寸（默认 1536；可改 1920）
    ap.add_argument("--det-side", type=int, default=1536,
                    help="text_det_limit_side_len，默认 1536（可调到 1920）")
    return ap.parse_args()

def _cuda_compiled() -> bool:
    try:
        if hasattr(paddle, 'is_compiled_with_cuda'):
            return bool(paddle.is_compiled_with_cuda())
        from paddle.fluid.core import is_compiled_with_cuda
        return bool(is_compiled_with_cuda())
    except Exception:
        return False

def main():
    args = parse_args()
    in_path = Path(args.input)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 设备
    if args.gpu:
        try:
            if _cuda_compiled():
                paddle.set_device('gpu'); device_str = 'gpu'
            else:
                print("[WARN] 当前 Paddle 未启用 CUDA，改用 CPU")
                paddle.set_device('cpu'); device_str = 'cpu'
        except Exception as e:
            print(f"[WARN] 设置 GPU 失败（{e}），改用 CPU")
            paddle.set_device('cpu'); device_str = 'cpu'
    else:
        paddle.set_device('cpu'); device_str = 'cpu'

    print(f"[INFO] Init PaddleOCR: lang={args.lang}, device={device_str}, angle_cls={args.angle_cls}")

    # 初始化 OCR（只调检测侧关键参数）
    ocr = PaddleOCR(
        lang=args.lang,
        use_textline_orientation=bool(args.angle_cls),
        use_doc_orientation_classify=True,
        use_doc_unwarping=True,

        # 关键三项（按你的建议范围设置）
        text_det_limit_side_len=int(args.det_side),  # 1536 ~ 1920
        text_det_limit_type="max",
        text_det_box_thresh=0.30,
        text_det_unclip_ratio=2.30,

        # 如需固定使用 v5 轻量模型，可解开：
        # text_detection_model_name="PP-OCRv5_mobile_det",
        # text_recognition_model_name="PP-OCRv5_mobile_rec",
    )

    imgs = collect_images(in_path)
    if not imgs:
        print(f"[WARN] 没有找到图片：{in_path}")
        sys.exit(1)
    if args.limit > 0:
        imgs = imgs[:args.limit]

    print(f"[INFO] 待处理图片数：{len(imgs)}")
    all_results: List[Dict[str, Any]] = []

    for idx, img_path in enumerate(imgs, 1):
        pad_color = _parse_color(args.pad_color)
        td_ctx, feed_path, (px, py), (orig_w, orig_h) = _make_padded_tmp(img_path, args.pad_ratio, pad_color)

        try:
            print(f"[{idx}/{len(imgs)}] OCR -> {img_path} (pad={args.pad_ratio:.2f}, det_side={args.det_side})")
            r = ocr_single(ocr, feed_path, debug_dir=(out_dir if args.debug else None))

            # 回退到原图坐标
            r["items"] = _shift_items_to_original(r.get("items", []), px, py, (orig_w, orig_h))
            r["image"] = str(img_path)
            all_results.append(r)

            if args.vis:
                vis_name = Path(img_path).stem + "_ocr_vis.jpg"
                visualize(img_path, r, out_dir / vis_name, font_path=args.font_path)

        except Exception as e:
            print(f"[ERROR] {img_path}: {e}")
        finally:
            if td_ctx is not None:
                td_ctx.cleanup()

    saved_any = False
    if args.save_json:
        save_json(all_results, out_dir / "results.json"); print(f"[OK] JSON -> {out_dir/'results.json'}"); saved_any = True
    if args.save_jsonl:
        save_jsonl(all_results, out_dir / "results.jsonl"); print(f"[OK] JSONL -> {out_dir/'results.jsonl'}"); saved_any = True
    if args.save_csv:
        save_csv(all_results, out_dir / "results.csv"); print(f"[OK] CSV -> {out_dir/'results.csv'}"); saved_any = True

    if args.vis:
        print(f"[OK] 可视化输出目录：{out_dir}")

    if not saved_any:
        print(json.dumps(all_results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
