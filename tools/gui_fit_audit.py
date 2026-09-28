"""Audits a GUI file for text that cannot fit: a fontsize set twice in one block
(the game keeps the first), fixed-size text with no fontsize_min to shrink into,
and boxes that reach past their parent's edge. Prints what it finds; changes
nothing. Usage: python tools/gui_fit_audit.py [file.gui]"""
import re
import sys

TEXTY = ('text_single', 'text_multi', 'button_regular', 'button_regular_alt', 'button_regular_alt_red',
         'button_regular_alt_green', 'button', 'textbox')


def parse(lines):
    """-> list of nodes: dict(name, start, end, parent, props{key: (lineno, value)})"""
    nodes, stack = [], []
    for i, raw in enumerate(lines):
        code = re.sub(r'"[^"]*"', '""', raw)
        code = re.sub(r'#.*', '', code)
        m = re.match(r'\s*([A-Za-z_][\w.]*)\s*=\s*\{\s*$', code)
        if m:
            node = {'name': m.group(1), 'start': i, 'end': None, 'parent': stack[-1] if stack else None,
                    'props': {}, 'dups': []}
            nodes.append(node)
            stack.append(node)
            continue
        m = re.match(r'\s*([A-Za-z_]\w*)\s*=\s*(.+?)\s*$', raw)
        if m and stack and code.count('{') == code.count('}'):
            key = m.group(1)
            if key in stack[-1]['props'] and key in ('fontsize', 'size', 'position'):
                stack[-1]['dups'].append((key, i))
            else:
                stack[-1]['props'][key] = (i, m.group(2))
        opens, closes = code.count('{'), code.count('}')
        if closes > opens:
            for _ in range(closes - opens):
                if stack:
                    stack.pop()['end'] = i
    return nodes


def num_pair(v):
    m = re.match(r'\{\s*(-?[\d.]+%?)\s+(-?[\d.]+%?)\s*\}', v or '')
    return (m.group(1), m.group(2)) if m else None


def resolve(n, axis):
    """a node's width (axis 0) / height (1) in pixels, following % to the parent"""
    p = n['props'].get('size')
    v = num_pair(p[1]) if p else None
    if not v:
        return None
    x = v[axis]
    if x.endswith('%'):
        par = n['parent']
        base = resolve(par, axis) if par else None
        return None if base is None else base * float(x[:-1]) / 100
    return float(x)


def main(path):
    lines = open(path, encoding='utf-8-sig').read().split('\n')
    nodes = parse(lines)
    dups = [(n, d) for n in nodes for d in n['dups'] if d[0] == 'fontsize']
    print('fontsize set twice in one block:', len(dups))
    nomin = [n for n in nodes if n['name'] in TEXTY and ('text' in n['props'] or 'raw_text' in n['props'])
             and 'fontsize' in n['props'] and 'fontsize_min' not in n['props'] and 'size' in n['props']]
    print('fixed-size text without fontsize_min:', len(nomin))
    spill = []
    for n in nodes:
        par = n['parent']
        if not par or 'size' not in n['props']:
            continue
        pw, w = resolve(par, 0), resolve(n, 0)
        pos = num_pair(n['props'].get('position', (0, '{ 0 0 }'))[1])
        if pw is None or w is None or not pos or pos[0].endswith('%'):
            continue
        over = float(pos[0]) + w - pw
        if over > 0.5 and 'parentanchor' not in n['props'] and 'widgetanchor' not in n['props']:
            spill.append((over, n['start'] + 1, n['name'], pos[0], w, pw))
    spill.sort(reverse=True)
    print('boxes reaching past their parent\'s right edge:', len(spill))
    for s in spill[:40]:
        print('  line %d %s: x=%s w=%g in %g -> %g px past' % (s[1], s[2], s[3], s[4], s[5], s[0]))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'in_game/gui/balance_colony_window.gui')
