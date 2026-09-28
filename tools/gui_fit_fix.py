"""Makes the colony window's text fit (see tools/gui_fit_audit.py):
  - a fontsize set twice in one block: the game keeps the first, so the
    second goes (the window looks as it did)
  - fixed-size text gets fontsize_min = 10, so what does not fit shrinks
    instead of running over its neighbour
  - text and edit boxes that start inside their parent but are 100% wide
    reached past its right edge by their offset: they get the parent's width
    less the offset on both sides
Usage: python tools/gui_fit_fix.py [file.gui]"""
import re
import sys

sys.path.insert(0, __file__.rsplit('/', 1)[0].rsplit('\\', 1)[0])
from gui_fit_audit import TEXTY, num_pair, parse, resolve  # noqa: E402

MIN = 10


def main(path):
    raw = open(path, encoding='utf-8-sig').read()
    lines = raw.split('\n')
    nodes = parse(lines)
    drop, insert_after, replace = set(), {}, {}
    for n in nodes:
        for key, i in n['dups']:
            if key == 'fontsize':
                drop.add(i)
        p = n['props']
        if (n['name'] in TEXTY and ('text' in p or 'raw_text' in p) and 'size' in p
                and 'fontsize' in p and 'fontsize_min' not in p):
            i, v = p['fontsize']
            if v.isdigit() and int(v) > MIN:
                ind = lines[i][:len(lines[i]) - len(lines[i].lstrip('\t'))]
                insert_after[i] = ind + 'fontsize_min = %d' % MIN
        # 100%-wide boxes set in from their parent's left edge
        size, pos = num_pair(p.get('size', (0, ''))[1]), num_pair(p.get('position', (0, '{ 0 0 }'))[1])
        par = n['parent']
        if size and pos and size[0] == '100%' and not pos[0].endswith('%') and float(pos[0]) > 0 and par:
            pw = resolve(par, 0)
            ph = resolve(par, 1)
            if pw:
                w = int(pw - 2 * float(pos[0]))
                h = size[1] if size[1].endswith('%') or ph is None else size[1]
                i = p['size'][0]
                replace[i] = re.sub(r'\{[^}]*\}', '{ %d %s }' % (w, h), lines[i], count=1)
    out = []
    for i, l in enumerate(lines):
        if i in drop:
            continue
        out.append(replace.get(i, l))
        if i in insert_after:
            out.append(insert_after[i])
    text = '\n'.join(out)
    bom = raw.startswith('﻿') or open(path, 'rb').read(3) == b'\xef\xbb\xbf'
    open(path, 'w', encoding='utf-8-sig' if bom else 'utf-8', newline='\n').write(text)
    print('%s: %d second fontsizes dropped, %d fontsize_min added, %d widths fixed'
          % (path, len(drop), len(insert_after), len(replace)))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'in_game/gui/balance_colony_window.gui')
