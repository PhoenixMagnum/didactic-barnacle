from __future__ import annotations

from pathlib import Path

from monakshi_os.rehearsal import evaluate_launch, render_markdown


def main():
    report = evaluate_launch()
    markdown = render_markdown(report)
    out = Path("data/launch_rehearsal.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(markdown, encoding="utf-8")
    print(markdown)
    print(f"\nSaved: {out}")


if __name__ == "__main__":
    main()
