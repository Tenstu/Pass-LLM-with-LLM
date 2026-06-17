"""rebuild_index.py — CLI 全量重建向量索引 + FTS 词法索引。

用法:
    python -m exam_memory.rebuild_index                # 全量重建
    python -m exam_memory.rebuild_index --type 算法    # 只重建指定类型
    python -m exam_memory.rebuild_index --force        # 强制覆盖已有索引
    python -m exam_memory.rebuild_index --fts-only     # 仅重建 FTS
    python -m exam_memory.rebuild_index --vec-only     # 仅重建向量
    python -m exam_memory.rebuild_index --dry-run      # 预览不写入
"""
from __future__ import annotations

import argparse
import glob
import sys
from datetime import datetime, timezone
from pathlib import Path


def _parse_fp(fp: str):
    text = Path(fp).read_text(encoding="utf-8")
    meta = {}
    body = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        try:
            import yaml
            meta = yaml.safe_load(parts[1]) or {}
        except Exception:
            pass
        body = parts[2].strip() if len(parts) >= 3 else ""
    name = Path(fp).name
    meta["file_name"] = name
    meta.setdefault("id", name)
    return meta, body


def main() -> int:
    ap = argparse.ArgumentParser(
        description="exam-memory 索引全量重建"
    )
    ap.add_argument("--type", choices=["单选题", "多选题", "算法"],
                    help="仅重建指定类型")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--verbose", "-v", action="store_true")
    ap.add_argument("--fts-only", action="store_true")
    ap.add_argument("--vec-only", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    from exam_memory.vector_store import BASE_DIR, NumpyVectorStore
    from exam_memory.fts_store import FTSStore
    from exam_memory.embedding import is_available, encode

    exp_dir = BASE_DIR / "experiences"
    type_filter = args.type

    all_files = glob.glob(str(exp_dir / "*.md"))
    if type_filter:
        files = [fp for fp in all_files
                 if _parse_fp(fp)[0].get("type") == type_filter]
    else:
        files = all_files

    if not files:
        print("[rebuild] experiences/ 为空，无需重建")
        return 0

    docs = [_parse_fp(fp) for fp in files]
    metas = [m for m, _ in docs]
    bodies = [b for _, b in docs]
    total_size = sum(len(b) for b in bodies)
    latest = max(Path(fp).stat().st_mtime for fp in files)
    latest_str = datetime.fromtimestamp(latest, tz=timezone.utc).isoformat()

    print(f"[rebuild] 扫描到 {len(files)} 条经验（{type_filter or '全部'}）")
    print(f"[rebuild] 签名: count={len(files)}, size={total_size}, mtime={latest_str}")

    if args.dry_run:
        print("[rebuild] dry-run，不写入")
        return 0

    do_vec = not args.fts_only
    if do_vec:
        if not is_available():
            print("[rebuild] embedding 不可用，跳过向量（pip install '.[embed]'）",
                  file=sys.stderr)
        else:
            store = NumpyVectorStore()
            skip = not args.force and store.is_available and not args.vec_only
            if skip:
                print(f"[rebuild] 向量索引已存在（{store.count} 条），加 --force 覆盖")
            else:
                print(f"[rebuild] 编码 {len(bodies)} 条...")
                embs = encode(bodies)
                if embs is not None:
                    store._embs = embs.astype("float32")
                    store._meta = []
                    for i, m in enumerate(metas):
                        m.setdefault("signature", {})["file_count"] = len(files)
                        m.setdefault("signature", {})["total_size"] = total_size
                        m.setdefault("signature", {})["latest_mtime"] = latest_str
                        m["schema_version"] = 2
                        store._meta.append(m)
                    store.save()
                    print(f"[rebuild] 向量完成: {len(metas)} 条, {store._embs.shape}")
                else:
                    print("[rebuild] 编码失败", file=sys.stderr)
                    return 1

    do_fts = not args.vec_only
    if do_fts:
        fts = FTSStore()
        n = fts.count()
        if n > 0 and not args.force:
            print(f"[rebuild] FTS 已存在（{n} 条），加 --force 覆盖")
        else:
            fts.clear()
            docs2 = [{"canonical_key": m.get("file_name", m.get("id", "")),
                      "title": m.get("title", m.get("knowledge", "")),
                      "knowledge": m.get("knowledge", ""),
                      "content": b, "type": m.get("type", "")}
                     for m, b in docs]
            fts.upsert_many(docs2)
            print(f"[rebuild] FTS 完成: {len(docs2)} 条")
        fts.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
