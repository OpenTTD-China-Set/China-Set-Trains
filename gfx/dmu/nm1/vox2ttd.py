#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""vox2ttd.py — 从 MagicaVoxel 色板生成 / 校验 gorender 的 ttd_palette.json

用法::

    python vox2ttd.py build MODEL.vox                     # JSON 输出到 stdout
    python vox2ttd.py build MODEL.vox -o ttd_palette.json # 写文件
    python vox2ttd.py build palette.png -o ttd_palette.json
    python vox2ttd.py build MODEL.vox --template 别的项目的/ttd_palette.json -o out.json
    python vox2ttd.py check MODEL.vox                     # 与参考色板逐项对比
    python vox2ttd.py check MODEL.vox --used              # 只看模型真正用到的色号
    python vox2ttd.py dump  MODEL.vox --used              # 逐色号明细
    python vox2ttd.py selftest                            # 内嵌数据自检

--------------------------------------------------------------------------
色号映射（实测确认，详见 README.md）
--------------------------------------------------------------------------
gorender 在 ``internal/voxelobject/processedvoxelobject.go`` 里做的是::

    p.Elements[x][y][z].Index = r.Voxels[x][y][z] - 2

``Voxels`` 是 gandalf 从 XYZI 里原样读出的 MagicaVoxel 色号（v，1..255，0 = 空），
两边都是 byte，所以 v=1 时 ``1-2`` 回绕成 255。于是::

    JSON 索引 = (v - 2) mod 256      <=>      entries[k] = 色板槽 (k + 2) mod 256

色板槽就是 MagicaVoxel 调色板面板里的第 v 格。**槽 0 不参与映射**（v 从 1 开始），
所以 JSON 索引 254 永远取不到，本工具用参考色板的第 254 项填它（见 --fill）。

.vox 的 RGBA chunk 与 MagicaVoxel 导出的色板 PNG 是同一份数组、同一顺序
（槽 1..槽 255，最后一项是槽 0），两者可互换。
"""

from __future__ import annotations

import argparse
import json
import struct
import sys
import zlib
from collections import Counter

VERSION = "1.0.0"

# --------------------------------------------------------------------------
# 内嵌参考数据
#
# TTD/DOS 调色板 256 色 + gorender 默认分段元数据，取自 gorender 仓库的
# files/ttd_palette.json（用 --template 可以换成任何项目自带的副本）。
# selftest 会校验这些数据自洽。
# --------------------------------------------------------------------------

TTD_LIGHTING = {
    "company_colour_lighting_contribution": 0.25,
    "default_brightness": 1.0,
    "company_colour_lighting_scale": 2.0,
}

TTD_RANGES = [
    {"_comment": "flat greys", "start": 1, "end": 15, "smoothness": -1},
    {"_comment": "blue greys", "start": 16, "end": 23, "smoothness": 1},
    {"_comment": "olive greens", "start": 24, "end": 31},
    {"_comment": "golden browns", "start": 32, "end": 39},
    {"_comment": "maroons", "start": 40, "end": 47},
    {"_comment": "pink flesh", "start": 48, "end": 49},
    {"_comment": "light yellows", "start": 50, "end": 52, "smoothness": -3},
    {"_comment": "tan browns", "start": 53, "end": 59},
    {"_comment": "yellow browns", "start": 60, "end": 63, "smoothness": -2},
    {"_comment": "yellows", "start": 64, "end": 69},
    {"_comment": "reddish browns", "start": 70, "end": 79},
    {"_comment": "company colour 2", "start": 80, "end": 87,
     "is_secondary_company_colour": True, "smoothness": 2},
    {"_comment": "forest greens", "start": 88, "end": 95},
    {"_comment": "mint greens", "start": 96, "end": 103},
    {"_comment": "forest browns", "start": 104, "end": 111, "smoothness": -1},
    {"_comment": "flesh tones", "start": 112, "end": 121},
    {"_comment": "maroon browns", "start": 122, "end": 127},
    {"_comment": "mauve (windows)", "start": 128, "end": 135, "smoothness": 2},
    {"_comment": "purples", "start": 136, "end": 143},
    {"_comment": "bright blues", "start": 144, "end": 153},
    {"_comment": "cyan blues", "start": 154, "end": 161},
    {"_comment": "pale reds", "start": 162, "end": 169},
    {"_comment": "saturated purples", "start": 170, "end": 177},
    {"_comment": "deep reds and yellows", "start": 178, "end": 191},
    {"_comment": "golden wheat", "start": 192, "end": 197},
    {"_comment": "company colour 1", "start": 198, "end": 205,
     "is_primary_company_colour": True, "smoothness": 2},
    {"_comment": "sage greens", "start": 206, "end": 209},
    {"_comment": "icy blues", "start": 210, "end": 214},
    {"_comment": "process pink", "start": 215, "end": 226, "is_process_colour": True},
    {"_comment": "block cycle", "start": 227, "end": 231, "is_animated_light": True},
    {"_comment": "fire cycle", "start": 232, "end": 238, "is_animated_light": True},
    {"_comment": "red flash", "start": 239, "end": 240, "smoothness": -2,
     "is_animated_light": True},
    {"_comment": "yellow blinker", "start": 241, "end": 244, "smoothness": -2,
     "is_animated_light": True},
    {"_comment": "water cycle", "start": 245, "end": 252, "is_animated_light": True},
    {"_comment": "cargopositor mask", "start": 253, "end": 255, "non_renderable": True},
]

# 256 项 RGB，每项 3 字节，共 768 字节
TTD_PALETTE_HEX = (
    "0000ff101010202020303030404040505050646464747474848484949494a8a8a8b8b8b8c8c8c8d8d8d8e8e8e8fcfcfc"
    "343c48444c5c5860706c7484848c989ca0acb0b8c4ccd0dc302c04403c0c504c14605c1c787840949464b0b084cccca8"
    "482c04583c1468502c7c684898845cb8a078d4bc94f4dcb0400004580410701020882034a0384cbc546ccc687cdc8490"
    "ec9ca4fcbcc0fcd000fce83cfcfc804c2800603c0874581c8874389c8850b09c6cc4b488441800602c048044089c6010"
    "b87818d49c20e8b810fcd400fcf880fcfcc0200400401408541c106c2c1c803828944838a85c4cb86c58c4806cd49480"
    "08340010400020500430600440700c54841468941c80a82c1c34182c44203c583050683c687c4c80945c98b06cb4cc7c"
    "10341820482c3860484c745860886c78a48898c0a8b8dcc8201800381c0048280458340c6840187c542c8c6c40a08058"
    "4c2810603418744428885438a46040b87050cc8060d49470e0a880ecbc94501c046428147838288c4c40a06460b88888"
    "2428443034544040645050746464888484a4acacc0d4d4e0281470402c905840ac684cc47858e08c68fca088fcbca8fc"
    "00186c0024840034a00048b80060d41878dc3890e858a8f080c4fcbce0fc10406018506c286078347084508ca074acc0"
    "9cccdcccf0fcac3434d43434fc3434fc6458fc907cfcb8a0fcd8c8fcf4ec4814705c2c8c7044a88c64c4a888e0c8b0f8"
    "d0b8ffe8d0fc3c00005c0000800000a00000c40000e00000fc0000fc5000fc6c00fc8800fca400fcc000fcdc00fcfc00"
    "cc8808e49004fc9c00fcb030fcc464fcd8980818580c246814347c1c448c285ca43878bc4898d864ace05c9c346cb040"
    "7cc84c90e05ce0f4fcc8ecf8b4dcec84bcd85898acf400f4f500f5f600f6f700f7f800f8f900f9fa00fafb00fbfc00fc"
    "fd00fdfe00feff00ff4c18086c2c18904834b06c54d2927efc3c00fc5400fc6800fc7c00fc9400fcac00fcc400400000"
    "ff0000303000404000505000ffff00204470244874284c782c507c3054804864906484a8d8f4fc6080a444608cffffff"
)

DEFAULT_MV_OFFSET = 2  # gorender: Index = Voxels - 2
RANGE_KEY_ORDER = ("_comment", "start", "end", "is_primary_company_colour",
                   "is_secondary_company_colour", "is_animated_light",
                   "is_process_colour", "smoothness", "non_renderable",
                   "max_gap_in_region", "expected_colour_range")


def reference_entries():
    """内嵌的 TTD 调色板 256 项 [(r, g, b), ...]。"""
    raw = bytes.fromhex(TTD_PALETTE_HEX)
    if len(raw) != 768:
        raise ValueError("内嵌色板长度异常：%d 字节" % len(raw))
    return [tuple(raw[i * 3:i * 3 + 3]) for i in range(256)]


def hex_of(rgb):
    return "#%02x%02x%02x" % tuple(rgb)


# --------------------------------------------------------------------------
# 色板来源
# --------------------------------------------------------------------------

class PaletteSource(object):
    """一个色板来源。

    slots[v] 是 MagicaVoxel 调色板第 v 格（v = 1..255）的颜色；
    slot0 是第 0 格（gorender 用不到，仅作记录）。
    used 仅在 .vox 来源下有意义：色号 -> 体素个数。
    """

    def __init__(self, path, kind):
        self.path = path
        self.kind = kind          # "vox" | "png"
        self.slots = {}
        self.slot0 = None
        self.used = Counter()
        self.notes = []
        self.vox_version = None
        self.models = 0
        self.voxel_count = 0
        self.size = None

    def usable_slots(self):
        return len(self.slots)


def _iter_chunks(buf):
    """按 VOX 规范遍历一段 chunk 序列：id(4) + content_size(4) + children_size(4)。"""
    off = 0
    end = len(buf)
    while off + 12 <= end:
        cid = buf[off:off + 4].decode("latin-1")
        content_size, children_size = struct.unpack_from("<ii", buf, off + 4)
        if content_size < 0 or children_size < 0:
            raise ValueError("chunk %r 的长度是负数，文件可能损坏" % cid)
        cstart = off + 12
        cend = cstart + content_size
        if cend + children_size > end:
            raise ValueError("chunk %r 超出文件末尾" % cid)
        yield cid, buf[cstart:cend], buf[cend:cend + children_size]
        off = cend + children_size


def load_vox(path):
    with open(path, "rb") as handle:
        buf = handle.read()

    if buf[:4] != b"VOX ":
        raise ValueError("%s 不是 MagicaVoxel 文件（缺少 'VOX ' 头）" % path)

    src = PaletteSource(path, "vox")
    src.vox_version = struct.unpack_from("<i", buf, 4)[0]

    rgba = None
    inner = []
    for cid, content, children in _iter_chunks(buf[8:]):
        if cid == "MAIN":
            inner.extend(_iter_chunks(children))
        else:  # 容错：有些写入器不套 MAIN
            inner.append((cid, content, children))

    for cid, content, _children in inner:
        if cid == "RGBA":
            rgba = content
        elif cid == "XYZI":
            if len(content) < 4:
                continue
            count = struct.unpack_from("<i", content, 0)[0]
            count = min(count, (len(content) - 4) // 4)
            src.models += 1
            for i in range(count):
                _x, _y, _z, colour = content[4 + i * 4:8 + i * 4]
                if colour != 0:
                    src.used[colour] += 1
                    src.voxel_count += 1
        elif cid == "SIZE" and len(content) >= 12:
            size = struct.unpack_from("<iii", content, 0)
            if src.size is None:
                src.size = size
            else:
                src.size = tuple(max(a, b) for a, b in zip(src.size, size))

    if rgba is None:
        src.notes.append("没有内嵌 RGBA chunk —— MagicaVoxel 只在色板被改动过时才写它；"
                         "该文件用的是 MagicaVoxel 默认色板，请改用 palette.png 或 --template")
    elif len(rgba) < 1024:
        src.notes.append("RGBA chunk 只有 %d 字节（应为 1024），色板不完整" % len(rgba))
    else:
        src.slot0 = tuple(rgba[255 * 4:255 * 4 + 3])
        for v in range(1, 256):
            src.slots[v] = tuple(rgba[(v - 1) * 4:(v - 1) * 4 + 3])

    return src


# ---------------------------------------------------------------- PNG 读取

def _unfilter(ftype, data, prev, bpp):
    """就地还原 PNG 扫描线滤波（PNG 规范 9.2）。data 不含滤波字节。"""
    n = len(data)
    if ftype == 0:
        return
    if ftype == 1:
        for i in range(bpp, n):
            data[i] = (data[i] + data[i - bpp]) & 0xFF
    elif ftype == 2:
        for i in range(n):
            data[i] = (data[i] + prev[i]) & 0xFF
    elif ftype == 3:
        for i in range(n):
            left = data[i - bpp] if i >= bpp else 0
            data[i] = (data[i] + ((left + prev[i]) >> 1)) & 0xFF
    elif ftype == 4:
        for i in range(n):
            left = data[i - bpp] if i >= bpp else 0
            up = prev[i]
            upleft = prev[i - bpp] if i >= bpp else 0
            p = left + up - upleft
            pa, pb, pc = abs(p - left), abs(p - up), abs(p - upleft)
            pred = left if (pa <= pb and pa <= pc) else (up if pb <= pc else upleft)
            data[i] = (data[i] + pred) & 0xFF
    else:
        raise ValueError("不认识的 PNG 滤波类型 %d" % ftype)


def _read_png_stdlib(path):
    """极简 PNG 解码（8 位 RGB/RGBA/灰度/调色板，非隔行）。返回 (w, h, pixels)。"""
    with open(path, "rb") as handle:
        data = handle.read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("%s 不是 PNG 文件" % path)

    ihdr, plte, trns, idat = None, None, None, bytearray()
    off = 8
    while off + 12 <= len(data):
        length = struct.unpack_from(">I", data, off)[0]
        ctype = data[off + 4:off + 8]
        chunk = data[off + 8:off + 8 + length]
        off += 12 + length
        if ctype == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", chunk)
        elif ctype == b"PLTE":
            plte = chunk
        elif ctype == b"tRNS":
            trns = chunk
        elif ctype == b"IDAT":
            idat += chunk
        elif ctype == b"IEND":
            break
    if ihdr is None:
        raise ValueError("%s 缺少 IHDR" % path)

    width, height, depth, colour_type, _comp, _filt, interlace = ihdr
    if interlace:
        raise ValueError("不支持隔行（Adam7）PNG，请安装 Pillow：pip install pillow")

    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(colour_type)
    if channels is None:
        raise ValueError("不支持的 PNG 颜色类型 %d" % colour_type)
    if depth not in (1, 2, 4, 8):
        raise ValueError("不支持的 PNG 位深 %d" % depth)

    raw = zlib.decompress(bytes(idat))
    bits_per_pixel = channels * depth
    stride = (width * bits_per_pixel + 7) // 8
    bpp = max(1, bits_per_pixel // 8)

    rows = []
    prev = bytearray(stride)
    pos = 0
    for _y in range(height):
        if pos + 1 + stride > len(raw):
            raise ValueError("PNG 数据不完整")
        ftype = raw[pos]
        line = bytearray(raw[pos + 1:pos + 1 + stride])
        pos += 1 + stride
        _unfilter(ftype, line, prev, bpp)
        rows.append(line)
        prev = line

    def samples(row):
        if depth == 8:
            return list(row[:width * channels])
        # 位深 < 8：只可能是灰度或调色板
        out = []
        per_byte = 8 // depth
        mask = (1 << depth) - 1
        for byte in row:
            for k in range(per_byte):
                shift = 8 - depth * (k + 1)
                out.append((byte >> shift) & mask)
        return out[:width * channels]

    pixels = []
    for row in rows:
        values = samples(row)
        for x in range(width):
            px = values[x * channels:(x + 1) * channels]
            if colour_type == 0:
                pixels.append((px[0], px[0], px[0], 255))
            elif colour_type == 2:
                pixels.append((px[0], px[1], px[2], 255))
            elif colour_type == 3:
                idx = px[0]
                if plte is None or idx * 3 + 2 >= len(plte):
                    raise ValueError("PNG 调色板项越界")
                alpha = 255
                if trns is not None and idx < len(trns):
                    alpha = trns[idx]
                pixels.append((plte[idx * 3], plte[idx * 3 + 1], plte[idx * 3 + 2], alpha))
            elif colour_type == 4:
                pixels.append((px[0], px[0], px[0], px[1]))
            else:
                pixels.append((px[0], px[1], px[2], px[3]))
    return width, height, pixels


def _read_png_pillow(path):
    from PIL import Image  # 可选依赖
    with Image.open(path) as image:
        image = image.convert("RGBA")
        width, height = image.size
        raw = image.tobytes()
    pixels = [tuple(raw[i:i + 4]) for i in range(0, len(raw), 4)]
    return width, height, pixels


_PNG_DECODER = "auto"


def read_png(path):
    if _PNG_DECODER == "stdlib":
        return _read_png_stdlib(path)
    if _PNG_DECODER == "pillow":
        return _read_png_pillow(path)
    try:
        return _read_png_pillow(path)
    except ImportError:
        return _read_png_stdlib(path)


def load_png(path):
    width, height, pixels = read_png(path)
    src = PaletteSource(path, "png")
    total = width * height
    if total != 256:
        raise ValueError("%s 是 %dx%d = %d 像素，色板图必须是 256 个像素"
                         "（MagicaVoxel 导出的是 256x1；16x16 也行）"
                         % (path, width, height, total))

    # MagicaVoxel 的色板数组顺序：槽 1..槽 255，最后一项是槽 0。
    src.slot0 = tuple(pixels[255][:3])
    for v in range(1, 256):
        src.slots[v] = tuple(pixels[v - 1][:3])
    if width != 256 or height != 1:
        src.notes.append("色板图是 %dx%d，已按栅格顺序当作 256 项处理" % (width, height))
    return src


def load_source(path):
    lowered = path.lower()
    if lowered.endswith(".vox"):
        return load_vox(path)
    if lowered.endswith(".png"):
        return load_png(path)
    raise ValueError("只认 .vox 与 .png，收到：%s" % path)


# --------------------------------------------------------------------------
# 映射
# --------------------------------------------------------------------------

def map_entries(src, offset):
    """把色板槽映射成 JSON entries。返回 (entries, unmapped)。

    entries[(v - offset) % 256] = slots[v]；槽 0 不参与，故 unmapped 是取不到的索引。
    """
    entries = [None] * 256
    for v in range(1, 256):
        rgb = src.slots.get(v)
        if rgb is None:
            continue
        entries[(v - offset) % 256] = rgb
    unmapped = [i for i, value in enumerate(entries) if value is None]
    return entries, unmapped


def fill_entries(entries, unmapped, filler):
    out = list(entries)
    for i in unmapped:
        out[i] = tuple(filler[i])
    return out


def range_lookup(ranges):
    table = {}
    for entry in ranges:
        for i in range(int(entry["start"]), int(entry["end"]) + 1):
            table.setdefault(i, entry)
    return table


def parse_index_list(text, size=256):
    """解析 ``215-226,253-255,80`` 形式的索引列表。"""
    out = []
    for part in (text or "").split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            first, last = part.split("-", 1)
            start, end = int(first), int(last)
        else:
            start = end = int(part)
        if start > end:
            start, end = end, start
        for i in range(start, end + 1):
            if 0 <= i < size:
                out.append(i)
    return sorted(set(out))


def range_flags(entry):
    if not entry:
        return ""
    flags = []
    if entry.get("is_primary_company_colour"):
        flags.append("公司色1")
    if entry.get("is_secondary_company_colour"):
        flags.append("公司色2")
    if entry.get("is_animated_light"):
        flags.append("动画光")
    if entry.get("is_process_colour"):
        flags.append("process(不渲染)")
    if entry.get("non_renderable"):
        flags.append("non_renderable")
    return ",".join(flags)


def render_json(entries, ranges, lighting, indent=2, eol="\n", final_newline=True):
    ordered_ranges = []
    for entry in ranges:
        ordered = {}
        for key in RANGE_KEY_ORDER:
            if key in entry:
                ordered[key] = entry[key]
        for key, value in entry.items():  # 保留自定义键（含其它 _comment）
            if key not in ordered:
                ordered[key] = value
        ordered_ranges.append(ordered)

    payload = {}
    for key in ("company_colour_lighting_contribution", "default_brightness",
                "company_colour_lighting_scale"):
        if key in lighting:
            payload[key] = lighting[key]
    payload["ranges"] = ordered_ranges
    payload["entries"] = [list(rgb) for rgb in entries]

    text = json.dumps(payload, indent=indent, ensure_ascii=False)
    if final_newline:
        text += "\n"
    if eol != "\n":
        text = text.replace("\n", eol)
    return text


def load_reference(template_path):
    """返回 (ranges, lighting, entries, 标签)。没有 --template 时用内嵌数据。"""
    if template_path:
        with open(template_path, "r", encoding="utf-8-sig") as handle:
            data = json.load(handle)
        entries = [tuple(item) for item in data["entries"]]
        if len(entries) != 256:
            raise ValueError("%s 的 entries 有 %d 项，应为 256" % (template_path, len(entries)))
        ranges = data.get("ranges", TTD_RANGES)
        lighting = {k: data[k] for k in TTD_LIGHTING if k in data}
        return ranges, lighting, entries, template_path
    return (json.loads(json.dumps(TTD_RANGES)), dict(TTD_LIGHTING),
            reference_entries(), "内嵌 TTD 参考")


# --------------------------------------------------------------------------
# 对比 / 报告
# --------------------------------------------------------------------------

def compare(entries, reference, ranges):
    """返回 (mismatch 列表, 每个 range 的归类)。"""
    mismatches = [i for i in range(256) if entries[i] != reference[i]]

    ref_values = set(reference)
    by_range = []
    covered = set()
    for entry in ranges:
        start, end = int(entry["start"]), int(entry["end"])
        idxs = list(range(start, end + 1))
        covered.update(idxs)
        bad = [i for i in idxs if i in set(mismatches)]
        if not bad:
            continue
        ref_set = sorted({reference[i] for i in idxs})
        got_set = sorted({entries[i] for i in idxs})
        if ref_set == got_set:
            kind = "颜色集合相同、排列顺序不同"
        elif all(value in ref_values for value in got_set):
            kind = "颜色取自参考色板、但落位不同"
        else:
            missing = [hex_of(v) for v in got_set if v not in ref_values]
            kind = "有参考色板里不存在的颜色：%s" % ", ".join(missing[:6])
        by_range.append((entry, bad, kind))

    leftover = [i for i in mismatches if i not in covered]
    return mismatches, by_range, leftover


def offset_scores(src, reference, candidates=(0, 1, 2, 3)):
    """每个候选偏移下，映射结果与参考色板的一致项数。"""
    scores = []
    for offset in candidates:
        entries, _unmapped = map_entries(src, offset)
        same = sum(1 for i in range(256)
                   if entries[i] is not None and entries[i] == reference[i])
        scores.append((offset, same))
    return scores


def print_offset_table(src, reference):
    print("色板槽 -> JSON 索引 偏移候选（gorender 的语义是 2）：")
    scores = offset_scores(src, reference)
    for offset, same in scores:
        print("   offset %d : 与参考一致 %3d / 256" % (offset, same))
    best = max(scores, key=lambda item: item[1])
    print("   最匹配的偏移 = %d" % best[0])
    return best[0]


# --------------------------------------------------------------------------
# 子命令
# --------------------------------------------------------------------------

def describe_source(src, stream=sys.stdout):
    kind = {"vox": "MagicaVoxel .vox（内嵌 RGBA 色板）", "png": "色板 PNG"}[src.kind]
    print("来源: %s" % src.path, file=stream)
    print("类型: %s" % kind, file=stream)
    if src.kind == "vox":
        print("VOX 版本: %s   模型数: %d   体素总数: %d   尺寸: %s"
              % (src.vox_version, src.models, src.voxel_count, src.size), file=stream)
        print("用到的色号: %d 个" % len(src.used), file=stream)
    print("可用色板槽: %d / 255" % src.usable_slots(), file=stream)
    print("槽 0（未使用）: %s" % (hex_of(src.slot0) if src.slot0 else "无"), file=stream)
    for note in src.notes:
        print("注意: %s" % note, file=stream)


def cmd_check(args):
    src = load_source(args.source)
    ranges, _lighting, reference, label = load_reference(args.template)
    table = range_lookup(ranges)

    describe_source(src)
    print("参考色板: %s" % label)
    print()

    if not src.slots:
        print("错误: 这个来源没有可用色板，无法校验。")
        return 2

    if args.mv_offset == "auto":
        offset = print_offset_table(src, reference)
        print()
    else:
        offset = int(args.mv_offset)

    entries, unmapped = map_entries(src, offset)
    filled = fill_entries(entries, unmapped, reference)

    mismatches, by_range, leftover = compare(filled, reference, ranges)

    if args.used:
        if src.kind != "vox":
            print("错误: --used 只对 .vox 有效（PNG 里没有模型信息）")
            return 2
        print("模型用到的色号（MV 色号 -> JSON 索引 -> 渲染时会发生什么）：")
        print("  %-6s %-6s %-9s %-9s %-8s %s"
              % ("MV色号", "索引", "颜色", "体素数", "渲染", "范围"))
        invisible = 0
        for colour in sorted(src.used):
            index = (colour - offset) % 256
            rgb = src.slots.get(colour)
            entry = table.get(index)
            flags = range_flags(entry)
            if index == 0:
                effect = "不可见(空)"
                invisible += src.used[colour]
            elif entry and entry.get("is_process_colour"):
                effect = "不可见(process)"
                invisible += src.used[colour]
            elif entry and entry.get("non_renderable"):
                effect = "不渲染"
            elif entry and (entry.get("is_primary_company_colour")
                            or entry.get("is_secondary_company_colour")):
                effect = "公司色替换"
            else:
                effect = "正常"
            comment = entry.get("_comment", "") if entry else ""
            print("  %-6d %-6d %-9s %-9d %-8s %s%s"
                  % (colour, index, hex_of(rgb) if rgb else "-", src.used[colour],
                     effect, comment, (" [%s]" % flags) if flags else ""))
        if invisible:
            print("  警告: 有 %d 个体素落在不可见的索引上，渲染时会消失。" % invisible)
        print()

    print("对比结果（偏移 %d）：%d / 256 项与参考一致，%d 项不同"
          % (offset, 256 - len(mismatches), len(mismatches)))
    if unmapped:
        print("  取不到的 JSON 索引（映射不到任何槽）: %s -> 已用参考值填充"
              % ", ".join(str(i) for i in unmapped))
    if mismatches:
        print("  不同项按范围归类：")
        for entry, bad, kind in by_range:
            print("    %3d-%3d %-24s %2d 项不同：%s"
                  % (entry["start"], entry["end"], entry.get("_comment", ""), len(bad), kind))
            if args.verbose:
                for i in bad:
                    print("        %3d  参考 %s   来源 %s"
                          % (i, hex_of(reference[i]), hex_of(filled[i])))
        if leftover:
            print("    (未落入任何范围: %s)" % ", ".join(str(i) for i in leftover))
        if args.show:
            print("  逐项差异：")
            for i in mismatches[:args.show]:
                print("    %3d  参考 %s   来源 %s" % (i, hex_of(reference[i]), hex_of(filled[i])))
            if len(mismatches) > args.show:
                print("    ...（还有 %d 项，用 --show 调大上限）" % (len(mismatches) - args.show))
    else:
        print("  完全一致。")

    if mismatches and not args.warn_only:
        return 1
    return 0


def cmd_build(args):
    src = load_source(args.source)
    ranges, lighting, reference, label = load_reference(args.template)

    if not src.slots:
        reason = "; ".join(src.notes) if src.notes else "文件里没有可读的色板数据"
        print("错误: 这个来源没有可用色板（%s）。" % reason, file=sys.stderr)
        return 2

    offset = args.mv_offset
    offset_note = ""
    if offset == "auto":
        scores = offset_scores(src, reference)
        chosen = max(scores, key=lambda item: item[1])
        offset = chosen[0]
        offset_note = "（auto 选定；" + "，".join(
            "%d:%d" % (value, same) for value, same in scores) + "）"
        print("偏移 auto -> %d %s" % (offset, offset_note), file=sys.stderr)
    offset = int(offset)
    entries, unmapped = map_entries(src, offset)

    if args.fill == "black":
        filler = [(0, 0, 0)] * 256
    elif args.fill == "white":
        filler = [(255, 255, 255)] * 256
    else:
        filler = reference
    entries = fill_entries(entries, unmapped, filler)

    if args.special_from_template:
        # process / non_renderable 两段的 RGB 被 gorender 忽略，改成沿用模板可以
        # 让生成结果与项目里既有的 ttd_palette.json 完全一致（少一堆无意义的 diff）。
        table = range_lookup(ranges)
        for i in range(256):
            entry = table.get(i)
            if entry and (entry.get("is_process_colour") or entry.get("non_renderable")):
                entries[i] = tuple(reference[i])

    # 项目自己塞在标准范围里的自定义色（例如 China-Set-* 把 215-226 改成 miku 等）
    # 不可能从通用的 .vox / palette.png 里读出来，只能显式指定沿用模板。
    for i in parse_index_list(args.template_entries_for):
        entries[i] = tuple(reference[i])

    text = render_json(entries, ranges, lighting, indent=args.indent,
                       eol="\r\n" if args.crlf else "\n",
                       final_newline=not args.no_final_newline)

    mismatches, _by_range, _left = compare(entries, reference, ranges)

    report = [
        "来源: %s (%s)" % (src.path, src.kind),
        "参考: %s" % label,
        "偏移: %d（gorender 的 Index = Voxels - %d）%s" % (offset, offset, offset_note),
        "取不到的 JSON 索引: %s（用 --fill 指定的值填充）"
        % (", ".join(str(i) for i in unmapped) if unmapped else "无"),
        "与参考色板相比: %d 项不同" % len(mismatches),
    ]

    if args.output:
        with open(args.output, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        report.append("已写入: %s" % args.output)
        print("\n".join(report))
        if mismatches and args.verbose:
            for i in mismatches:
                print("  差异 %3d  参考 %s   输出 %s"
                      % (i, hex_of(reference[i]), hex_of(entries[i])))
    else:
        print(text, end="")
        print("\n".join(report), file=sys.stderr)
    return 0


def cmd_dump(args):
    src = load_source(args.source)
    ranges, _lighting, reference, label = load_reference(args.template)
    table = range_lookup(ranges)
    if args.mv_offset == "auto":
        offset = max(offset_scores(src, reference), key=lambda item: item[1])[0]
    else:
        offset = int(args.mv_offset)

    describe_source(src)
    print("参考: %s   偏移: %d" % (label, offset))
    print()
    print("  %-6s %-6s %-9s %-9s %-16s %s"
          % ("MV色号", "索引", "颜色", "体素数", "范围", "状态"))
    print("  " + "-" * 78)

    if args.used:
        if src.kind != "vox":
            print("错误: --used 只对 .vox 有效")
            return 2
        colours = sorted(src.used)
    else:
        colours = [v for v in range(1, 256) if v in src.slots]

    for v in colours:
        rgb = src.slots.get(v)
        index = (v - offset) % 256
        entry = table.get(index)
        count = src.used.get(v, 0) if src.kind == "vox" else -1
        status = []
        if rgb == reference[index]:
            status.append("=参考")
        else:
            status.append("≠参考(%s)" % hex_of(reference[index]))
        if index == 0:
            status.append("不可见:空")
        if entry and entry.get("is_process_colour"):
            status.append("不可见:process")
        print("  %-6d %-6d %-9s %-9s %-16s %s"
              % (v, index, hex_of(rgb) if rgb else "-",
                 count if count >= 0 else "-",
                 entry.get("_comment", "") if entry else "",
                 " ".join(status)))
    return 0


def cmd_selftest(_args):
    ok = True
    entries = reference_entries()
    print("1) 内嵌色板: %d 项，长度 %d 字节" % (len(entries), len(bytes.fromhex(TTD_PALETTE_HEX))))
    if len(entries) != 256 or len(bytes.fromhex(TTD_PALETTE_HEX)) != 768:
        ok = False
        print("   失败: 长度不对")

    table = range_lookup(TTD_RANGES)
    missing = [i for i in range(256) if i not in table]
    overlaps = []
    seen = set()
    for entry in TTD_RANGES:
        for i in range(entry["start"], entry["end"] + 1):
            if i in seen:
                overlaps.append(i)
            seen.add(i)
    print("2) ranges 覆盖: %d / 256，重叠: %s" % (len(seen), overlaps or "无"))
    if missing == [0]:
        print("   只有索引 0 不在任何 range 里 —— 正常（TTD 特殊蓝，gorender 把索引 0 当空体素）")
    elif missing:
        print("   失败: 未覆盖索引 %s" % missing)
        ok = False
    if overlaps:
        ok = False

    print("3) 映射往返: 由内嵌色板造出 255 个槽，再映射回 entries")
    src = PaletteSource("(selftest)", "vox")
    for v in range(1, 256):
        src.slots[v] = entries[(v - DEFAULT_MV_OFFSET) % 256]
    src.slot0 = (0, 0, 0)
    back, unmapped = map_entries(src, DEFAULT_MV_OFFSET)
    back = fill_entries(back, unmapped, entries)
    same = sum(1 for i in range(256) if back[i] == entries[i])
    print("   往返一致: %d / 256，取不到的索引: %s" % (same, unmapped))
    if same != 256:
        fail = [i for i in range(256) if back[i] != entries[i]]
        print("   失败索引: %s" % fail)
        ok = False

    print("4) JSON 生成: 键序与规范一致")
    text = render_json(entries, TTD_RANGES, TTD_LIGHTING)
    data = json.loads(text)
    keys = list(data.keys())
    expect = ["company_colour_lighting_contribution", "default_brightness",
              "company_colour_lighting_scale", "ranges", "entries"]
    print("   顶层键: %s" % keys)
    if keys != expect:
        ok = False
        print("   失败: 期望 %s" % expect)
    if [tuple(x) for x in data["entries"]] != entries:
        ok = False
        print("   失败: entries 往返不一致")

    print()
    print("selftest: %s" % ("通过" if ok else "失败"))
    return 0 if ok else 1


# --------------------------------------------------------------------------

def build_parser():
    parser = argparse.ArgumentParser(
        prog="vox2ttd.py",
        description="从 MagicaVoxel 色板（.vox 内嵌 RGBA 或色板 PNG）生成 gorender 的 "
                    "ttd_palette.json",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="映射关系: JSON entries[k] = 色板槽 (k + %d) mod 256（gorender 的 "
               "Index = Voxels - %d）" % (DEFAULT_MV_OFFSET, DEFAULT_MV_OFFSET))
    parser.add_argument("--version", action="version", version="vox2ttd %s" % VERSION)
    sub = parser.add_subparsers(dest="command")

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("source", nargs="?", help=".vox 或色板 .png")
    common.add_argument("--template", metavar="JSON",
                        help="沿用这个 ttd_palette.json 的 ranges 与光照参数"
                             "（默认用内嵌的 TTD 官方分段）")
    common.add_argument("--mv-offset", default=str(DEFAULT_MV_OFFSET),
                        help="MV 色号到 JSON 索引的偏移，默认 %d；填 auto 让工具按参考色板自动挑"
                             % DEFAULT_MV_OFFSET)
    common.add_argument("--png-decoder", choices=("auto", "pillow", "stdlib"), default="auto",
                        help="读色板 PNG 的解码器：auto 优先用 Pillow，没有就用内置解码器")

    p_build = sub.add_parser("build", parents=[common], help="生成 ttd_palette.json")
    p_build.add_argument("-o", "--output", metavar="JSON",
                         help="输出文件；不给就打到 stdout")
    p_build.add_argument("--fill", choices=("template", "black", "white"), default="template",
                         help="填不可达索引（默认取参考色板的对应项）")
    p_build.add_argument("--special-from-template", action="store_true",
                         help="process / non_renderable 两段（RGB 会被 gorender 忽略）沿用模板，"
                              "便于与既有 ttd_palette.json 完全对齐")
    p_build.add_argument("--template-entries-for", default="", metavar="索引",
                         help="这些 JSON 索引沿用模板的颜色，写法如 215-226,253-255。"
                              "用于项目把自定义色塞进标准范围、而色板来源里没有这些颜色的情况")
    p_build.add_argument("--indent", type=int, default=2)
    p_build.add_argument("--crlf", action="store_true", help="用 CRLF 换行（对齐旧文件）")
    p_build.add_argument("--no-final-newline", action="store_true")
    p_build.add_argument("-v", "--verbose", action="store_true")
    p_build.set_defaults(func=cmd_build)

    p_check = sub.add_parser("check", parents=[common],
                             help="与参考色板逐项对比（不同则退出码 1）")
    p_check.add_argument("--used", action="store_true", help="只看模型真正用到的色号")
    p_check.add_argument("--verbose", action="store_true", help="列出范围内每个差异项")
    p_check.add_argument("--show", type=int, default=0, metavar="N",
                         help="另外列出前 N 个差异项")
    p_check.add_argument("--warn-only", action="store_true", help="无论是否不同都退出 0")
    p_check.set_defaults(func=cmd_check)

    p_dump = sub.add_parser("dump", parents=[common], help="逐色号打印明细")
    p_dump.add_argument("--used", action="store_true", help="只列模型用到的色号")
    p_dump.set_defaults(func=cmd_dump)

    p_self = sub.add_parser("selftest", help="校验内嵌参考数据与映射自洽")
    p_self.set_defaults(func=cmd_selftest)

    return parser


def main(argv=None):
    global _PNG_DECODER
    # Windows 控制台/管道默认按本地代码页编码，中文会乱码；统一走 UTF-8。
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError, OSError):
            pass

    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 2
    if args.func is not cmd_selftest and not args.source:
        parser.error("缺少 source（.vox 或 .png）")
    _PNG_DECODER = getattr(args, "png_decoder", "auto")
    try:
        return args.func(args)
    except (OSError, ValueError) as exc:
        print("错误: %s" % exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
