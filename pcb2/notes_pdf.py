"""把 fab/MANUFACTURING-NOTES.md 轉成 PDF（中英文）。"""
import os, markdown
from weasyprint import HTML
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fab')
md = open(os.path.join(D, 'MANUFACTURING-NOTES.md'), encoding='utf-8').read()
body = markdown.markdown(md, extensions=['tables'])
css = """@page { size: A4; margin: 16mm 14mm; @bottom-right { content: counter(page) ' / ' counter(pages); font-size: 8pt; color: #888; } }
body { font-family: 'Noto Sans CJK TC', 'DejaVu Sans', sans-serif; font-size: 9.5pt; line-height: 1.5; color: #1d1d1f; }
h1 { font-size: 15pt; margin: 0 0 4pt; } h2 { font-size: 12pt; margin: 14pt 0 4pt; border-bottom: 1px solid #ccc; padding-bottom: 2pt; }
table { border-collapse: collapse; width: 100%; margin: 4pt 0 8pt; font-size: 8.8pt; }
th, td { border: 1px solid #ccc; padding: 3pt 5pt; text-align: left; vertical-align: top; } th { background: #f2f2f2; }
code { font-family: 'DejaVu Sans Mono', monospace; font-size: 8.5pt; background: #f4f4f4; padding: 0 2pt; }
hr { border: none; border-top: 1px solid #ddd; }"""
HTML(string=f'<html><head><meta charset="utf-8"><style>{css}</style></head><body>{body}</body></html>').write_pdf(os.path.join(D, 'MANUFACTURING-NOTES.pdf'))
print('ok')
