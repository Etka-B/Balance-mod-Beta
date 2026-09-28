"""Keeps the colony window's list rows clear of their card's rolled edges.

The rows are drawn on bg_scroll_card, a strip of paper whose left and right
ends curl over for about 9 px (measured in game at 100% scale). Icons, flags
and checkboxes set 4-9 px in sat on the curl, and a few boxes on the right
reached into it. Every row's content now keeps 12 px from the left end and
11 px from the right; the building picker also gets the room its long names
need (the space to the right of its Forbidden column was unused).

Each rule names a row by its card's width and a child by its old position
(and size), so rerunning the script changes nothing. Rerun it after the
window is regenerated: python tools/gui_card_padding.py
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gui_fit_audit import parse, resolve  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GUI = os.path.join(ROOT, 'in_game/gui/balance_colony_window.gui')

# (card width, path of child names from the card, old position, old size,
#  new position, new size); a path of two names is a box inside a box, the
#  first given as name@position of the outer box before the change.
RULES = [
    # the subjects list
    (253, ['country_flag_small'], '9 9', None, '12 9', None),
    (253, ['text_single'], '56 4', '188 19', None, '186 19'),
    (253, ['text_single'], '56 23', '188 17', None, '186 17'),
    # the locations list: its checkbox, and the Local governor column
    (739, ['button_checkbox'], '6 8', '24 24', '12 8', None),
    (739, ['widget'], '603 4', '127 30', '601 4', None),
    # a location's buildings
    (393, ['icon'], '9 9', '32 32', '12 9', None),
    (393, ['text_single'], '266 4', '119 22', None, '116 22'),
    (393, ['text_single'], '222 31', '162 19', None, '160 19'),
    # the building picker: room for "Republican Assembly" and "Forbidden"
    (376, ['icon'], '4 2', '32 32', '12 2', None),
    (376, ['text_single'], '43 9', '127 19', '50 9', '146 19'),
    (376, ['widget'], '173 4', '86 28', '198 4', '76 28'),
    (376, ['widget@173 4', 'text_single'], '35 0', '50 28', '31 0', '45 28'),
    (376, ['widget'], '261 4', '93 28', '276 4', '88 28'),
    (376, ['widget@261 4', 'text_single'], '35 0', '56 28', '31 0', '57 28'),
    # the raw material picker
    (376, ['text_single'], '43 9', '216 19', '50 9', '209 19'),
    # the priority rows: their number
    (739, ['widget'], '6 6', '28 28', '12 6', '26 28'),
    # the level popup (tools/colony_tier_gui_patch.py)
    (390, ['icon'], '6 4', '34 34', '12 4', None),
    (390, ['text_single'], '48 10', '200 22', '52 10', '192 22'),
    (390, ['text_single'], '252 10', '130 22', '248 10', '128 22'),
    (390, ['button_regular'], '262 7', '120 28', '258 7', '118 28'),
    # colony assignment: its rows' button, its options, its subjects
    (726, ['button_minimize'], '687 9', '30 30', '685 9', None),
    (667, ['button_checkbox_round'], '4 4', '24 24', '12 4', None),
    (667, ['text_single'], '35 0', '631 32', '42 0', '614 32'),
    (650, ['country_flag_small'], '9 8', None, '12 8', None),
    (650, ['widget'], '477 8', '164 28', '475 8', None),
    # the province list and the row's location box
    (264, ['text_single'], '11 6', '244 19', '12 6', '241 19'),
    (773, ['widget'], '6 5', '86 26', '12 5', None),
    (773, ['text_single'], '624 10', '140 19', None, '138 19'),
]


def val(node, key):
    p = node['props'].get(key)
    return re.sub(r'\s+', ' ', p[1].strip('{} ')) if p else None


def main():
    text = open(GUI, encoding='utf-8-sig').read()
    lines = text.split('\n')
    nodes = parse(lines)
    cards = [n for n in nodes if val(n, 'using') == 'bg_scroll_card']
    edits, hits = {}, [0] * len(RULES)
    for card in cards:
        width = resolve(card, 0)
        for r, (w, path, pos, size, npos, nsize) in enumerate(RULES):
            if width != w:
                continue
            parents = [card]
            for step in path[:-1]:
                name, at = step.split('@')
                parents = [k for k in nodes if k['parent'] in parents and k['name'] == name and val(k, 'position') == at]
            for k in nodes:
                if (k['parent'] in parents and k['name'] == path[-1] and val(k, 'position') == pos
                        and (size is None or val(k, 'size') == size)):
                    hits[r] += 1
                    for key, new in (('position', npos), ('size', nsize)):
                        if new:
                            i = k['props'][key][0]
                            edits[i] = re.sub(r'\{[^}]*\}', '{ %s }' % new, lines[i], count=1)
    for i, l in edits.items():
        lines[i] = l
    open(GUI, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines))
    for (w, path, pos, *_), n in zip(RULES, hits):
        print('%4d x  card %d  %s at %s' % (n, w, '/'.join(path), pos))
    print(len(edits), 'lines changed')


if __name__ == '__main__':
    main()
