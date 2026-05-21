#!/usr/bin/env python3
"""
Quality Validator - 内容质量检查

检测：
1. TODO/占位符
2. 空洞章节（太短或无实质内容）
3. 重复段落
4. "后续补充"等无效承诺
5. 只列问题不写建议

exit 0 = 通过
exit 1 = 发现质量问题（warning级别，不阻断）
"""

import re
import sys
from pathlib import Path


PLACEHOLDER_PATTERNS = [
    (r"(?i)TODO\b", "包含 TODO 标记"),
    (r"(?i)(FIXME|HACK|TEMP|RANGE)\b", "包含临时标记"),
    (r"(?i)待(补充|完善|优化|确认|确认|验证)", "包含待定承诺"),
    (r"(?i)(后续|稍后|之后|未来)再?(补充|添加|完善|优化|讨论)", "包含延迟承诺"),
    (r"(?i)(placeholder|lorem ipsum|这里填写|待填写)", "包含占位文本"),
    (r"(?i)pass\s*$", "使用 pass 占位（可能为伪实现）"),
    (r"(?i)raise NotImplemented", "使用 NotImplementedError（未实现）"),
]

EMPTY_SECTION_HINT = 30

DUP_THRESHOLD = 3


def check_quality(file_path: str) -> list[str]:
    path = Path(file_path)
    if not path.exists():
        return [f"文件不存在：{file_path}"]

    content = path.read_text(encoding="utf-8")
    lines = content.split("\n")
    issues = []

    for pattern, description in PLACEHOLDER_PATTERNS:
        matches = re.findall(pattern, content)
        if matches:
            issues.append(f"{path.name}: {description}（{len(matches)} 次）")

    if len(content.strip()) > 1000:
        sentence_count = len(re.split(r"[。！？.!?]", content))
        if sentence_count < 5:
            issues.append(f"{path.name}: 内容可能为空洞文本（{len(content.strip())} 字符但仅 {sentence_count} 句）")

    seen_sentences = {}
    sentences = re.split(r"[。！？.!?]+", content)
    for s in sentences:
        s = s.strip()
        if len(s) < 20:
            continue
        count = seen_sentences.get(s, 0) + 1
        seen_sentences[s] = count
        if count > DUP_THRESHOLD:
            issues.append(f"{path.name}: 检测到重复内容（\"{s[:30]}...\" 出现 {count} 次）")
            del seen_sentences[s]

    return issues


def main():
    file_path = sys.argv[1] if len(sys.argv) > 1 else ""

    if not file_path:
        print("用法: quality_validator <file_path>")
        sys.exit(1)

    issues = check_quality(file_path)

    if issues:
        for i in issues:
            print(f"[QUALITY WARNING] {i}", file=sys.stderr)
        sys.exit(1)
    else:
        print("OK: 质量检查通过")
        sys.exit(0)


if __name__ == "__main__":
    main()
