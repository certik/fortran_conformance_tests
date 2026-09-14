#!/usr/bin/env python3
"""Inventory the pinned PDF without redistributing its body text.

PyMuPDF is an authoring dependency; the test runner remains stdlib-only.
The document-specific typography rules are guarded by the PDF checksum.
List items and table rows still need a reviewed fine-grained census.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re


PDF_SHA256 = '7371e889f231cfb0316d30365d5083fb5af34cbb6d5f7cb1e01855c73021bfa2'
SECTION = re.compile(r'(?:[1-9]\d?|[ABC])(?:\.[1-9]\d*)*')
ROOT = Path(__file__).resolve().parents[1]


def rows(page):
    spans = []
    for block in page.get_text('dict')['blocks']:
        for line in block.get('lines', []):
            for span in line['spans']:
                x0, y0, x1, y1 = span['bbox']
                if 60 < y0 < page.rect.height - 50 and x0 >= 32 and span['text'].strip():
                    spans.append(dict(span, center=(y0 + y1) / 2))
    grouped = []
    for span in sorted(spans, key=lambda value: (value['center'], value['bbox'][0])):
        if not grouped or abs(span['center'] - grouped[-1][0]) > 2.5:
            grouped.append((span['center'], []))
        grouped[-1][1].append(span)
    for _, line in grouped:
        line.sort(key=lambda value: value['bbox'][0])
        if line[0]['bbox'][1] > 750 and any('J3/24-007' in span['text'] for span in line):
            continue
        yield line


def heading(line):
    first = line[0]
    text = first['text'].strip()
    if 'LMSans' not in first['font'] or 'Bold' not in first['font']:
        return None
    if not 55 <= first['bbox'][0] <= 61:
        return None
    if SECTION.fullmatch(text) and text not in ('A', 'B', 'C'):
        return text
    combined = ' '.join(span['text'].strip() for span in line)
    annex = re.match(r'^Annex ([ABC])\b', combined)
    return annex.group(1) if annex else None


def unit_label(line, known_rules):
    first = line[0]
    text = first['text'].strip()
    if first['font'].startswith('LMSans9') and 47 <= first['bbox'][2] <= 51 and text.isdigit():
        return 'p' + text, 'paragraph'
    if 55 <= first['bbox'][0] <= 61 and text in known_rules:
        return text, 'numbered-item'
    combined = ' '.join(span['text'].strip() for span in line)
    if 'LMMono' not in first['font']:
        caption = re.match(r'^(Table|Figure)\s+((?:\d+|[ABC])\.\d+)\s*[:\u2014-]', combined)
        if caption and 'Bold' in first['font']:
            kind = caption.group(1).lower()
            return kind + caption.group(2), kind
        entry_note = re.match(r'^Note (\d+) to entry:', combined)
        if entry_note:
            return 'note-entry' + entry_note.group(1), 'note'
        note = re.match(r'^NOTE(?:\s+(\d+))?(?:\s|$)', combined)
        if note:
            return 'note' + (note.group(1) or '-unnumbered'), 'note'
    return None


def inventory(pdf_path, rules_path):
    import fitz

    data = pdf_path.read_bytes()
    if hashlib.sha256(data).hexdigest() != PDF_SHA256:
        raise ValueError('PDF checksum differs from the pinned J3/24-007 document')
    known = set(re.findall(r'^([RC]\d+)\b', rules_path.read_text(), re.M))
    document = fitz.open(stream=data, filetype='pdf')
    outline = document.get_toc()
    index_page = next(page for _, title, page in outline if title == 'Index')
    numbered_outline = {
        match.group(1)
        for _, title, _ in outline
        if (match := re.match(r'^((?:[1-9]\d?|[ABC])(?:\.[1-9]\d*)*)\s', title))
    }
    annex_starts = {
        page: match.group(1)
        for level, title, page in outline
        if level == 1 and (match := re.match(r'^(?:Annex\s+)?([ABC])(?:\s|$)', title))
    }
    sections = {}
    current = None
    active = None
    for page_number in range(14, index_page - 1):
        if page_number + 1 in annex_starts:
            current = annex_starts[page_number + 1]
            sections[current] = dict(pdf_page=page_number + 1, units={}, fragments=[])
            active = None
        for line in rows(document[page_number]):
            section = heading(line)
            if section:
                if section in sections:
                    if section in ('A', 'B', 'C') and sections[section]['pdf_page'] == page_number + 1:
                        continue
                    raise ValueError(f'duplicate section heading {section} on PDF page {page_number + 1}')
                sections[section] = dict(pdf_page=page_number + 1, units={}, fragments=[])
                current, active = section, None
                continue
            if current is None:
                continue
            text = ' '.join(span['text'].strip() for span in line)
            sections[current]['fragments'].append(text)
            label = unit_label(line, known)
            if label:
                name, kind = label
                units = sections[current]['units']
                if name in units:
                    if kind == 'paragraph':
                        raise ValueError(f'duplicate {current}#{name}; inspect heading extraction')
                    if kind != 'table':
                        suffix = 2
                        while name + '.' + str(suffix) in units:
                            suffix += 1
                        name += '.' + str(suffix)
                if name not in units:
                    units[name] = dict(kind=kind, pdf_page=page_number + 1, fragments=[])
                active = name
            if active is None:
                active = 'body'
                sections[current]['units'].setdefault(
                    active, dict(kind='unlabelled-text', pdf_page=page_number + 1, fragments=[]))
            sections[current]['units'][active]['fragments'].append(text)
    missing_headings = numbered_outline - set(sections)
    if missing_headings:
        raise ValueError('outline headings missing from body inventory: ' + ', '.join(sorted(missing_headings)))
    found = {name for section in sections.values() for name in section['units'] if name in known}
    if found != known:
        raise ValueError('numbered items missing from PDF inventory: ' + ', '.join(sorted(known - found)))
    for section in sections.values():
        section['sha256'] = hashlib.sha256('\n'.join(section.pop('fragments')).encode()).hexdigest()
        for unit in section['units'].values():
            unit['sha256'] = hashlib.sha256('\n'.join(unit.pop('fragments')).encode()).hexdigest()
    return dict(
        schema_version=1, document='J3/24-007', edition='F2023', sha256=PDF_SHA256,
        pdf_pages=len(document),
        extraction='Pinned typography: body headings, paragraph labels, numbered items, table captions, notes; '
                   'unlabelled text retained. List/table subdivisions require review.',
        non_numbered_sections=[dict(id=title.lower().replace(' ', '-'), pdf_page=page, disposition='structural')
                               for _, title, page in outline if title in ('Contents', 'Foreword', 'Introduction', 'Index')],
        sections=sections)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('pdf', type=Path)
    parser.add_argument('--rules', type=Path, default=ROOT / 'doc/fortran_2023_rules.txt')
    parser.add_argument('--output', type=Path, default=ROOT / 'doc/source_inventory.json')
    args = parser.parse_args()
    result = inventory(args.pdf, args.rules)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    units = sum(len(section['units']) for section in result['sections'].values())
    print(f"Indexed {len(result['sections'])} sections and {units} source units; no body text stored.")


if __name__ == '__main__':
    main()
