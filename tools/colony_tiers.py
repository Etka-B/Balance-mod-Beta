"""Writes the colony window's building-level scripts from the building types.

A building's levels are the game's upgrade chains: a building type that says
`obsolete = X` replaces X (marketplace -> merchants_quarters -> ...). The game
gives script no way to read that, so this reads every `obsolete = ...` line in
in_game/common/building_types/*.txt and writes the chains out as triggers and
effects:

  in_game/common/scripted_triggers/balance_colony_tier_triggers.txt
  in_game/common/scripted_effects/balance_colony_tier_effects.txt
  in_game/common/scripted_guis/balance_colony_tier_gui.txt

Rerun it after a game update (from the mod folder: python tools/colony_tiers.py).
"""
import collections
import glob
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROWS = 20


def read_chains():
    defs = {}
    for path in sorted(glob.glob(os.path.join(ROOT, 'in_game/common/building_types/*.txt'))):
        s = open(path, encoding='utf-8-sig').read()
        for m in re.finditer(r'^﻿?((?:TRY_REPLACE:|REPLACE:)?)([a-z_0-9]+)\s*=\s*\{', s, re.M):
            start = m.end()
            depth, i = 1, start
            while depth and i < len(s):
                depth += (s[i] == '{') - (s[i] == '}')
                i += 1
            body = s[start:i]
            obs = re.findall(r'^\tobsolete\s*=\s*(\w+)', body, re.M)
            # a REPLACE: wins over the plain copy
            if m.group(2) not in defs or m.group(1):
                defs[m.group(2)] = obs
    pred = collections.defaultdict(list)
    for new, olds in defs.items():
        for old in olds:
            if old in defs:
                pred[new].append(old)
    graph = collections.defaultdict(set)
    for new, olds in pred.items():
        for old in olds:
            graph[new].add(old)
            graph[old].add(new)

    memo = {}

    def depth(x):
        if x not in memo:
            memo[x] = 0 if not pred[x] else 1 + max(depth(p) for p in pred[x])
        return memo[x]

    seen, chains = set(), []
    for x in sorted(graph):
        if x in seen:
            continue
        stack, comp = [x], set()
        while stack:
            y = stack.pop()
            if y not in comp:
                comp.add(y)
                stack.extend(graph[y])
        seen |= comp
        chains.append(sorted(comp, key=lambda b: (depth(b), b)))
    chains.sort(key=lambda c: c[0])
    return chains, {k: sorted(v) for k, v in pred.items() if v}


HEADER = '# Written by tools/colony_tiers.py from the building types\' obsolete = ... lines;\n# rerun it after a game update rather than editing this file.\n'


def write(rel, text):
    path = os.path.join(ROOT, rel)
    with open(path, 'w', encoding='utf-8-sig', newline='\n') as f:
        f.write(text)
    print('wrote', rel)


def main():
    chains, pred = read_chains()
    members = [b for c in chains for b in c]

    # ---- triggers
    t = ['# THE COLONY WINDOW\'S BUILDING LEVELS (gui/balance_colony_window.gui).', HEADER]
    t.append('# subject scope: row S holds a building that has other levels')
    t.append('balance_tier_row_has_chain = {\n\tOR = {')
    t += ['\t\tvar:balance_prio_$S$_b ?= building_type:%s' % b for b in members]
    t.append('\t}\n}\n')
    t.append('# subject scope: row S holds a building that replaces an older one, so it can be\n# ordered as an upgrade ("Where: upgrades only")')
    t.append('balance_prio_row_can_upgrade = {\n\tOR = {')
    t += ['\t\tvar:balance_prio_$S$_b ?= building_type:%s' % b for b in sorted(pred)]
    t.append('\t}\n}\n')
    t.append('# location scope (scope:balance_prio_t = the row\'s building, scope:balance_prio_c =\n# the subject): an older level of it, the subject\'s own, stands here. Building it\n# here replaces that one.')
    t.append('balance_prio_has_predecessor_here = {\n\tOR = {')
    for new in sorted(pred):
        olds = pred[new]
        t.append('\t\tAND = {')
        t.append('\t\t\tscope:balance_prio_t = building_type:%s' % new)
        t.append('\t\t\tany_buildings_in_location = {')
        t.append('\t\t\t\towner ?= scope:balance_prio_c')
        if len(olds) == 1:
            t.append('\t\t\t\tbuilding_type = building_type:%s' % olds[0])
        else:
            t.append('\t\t\t\tOR = { %s }' % ' '.join('building_type = building_type:%s' % o for o in olds))
        t.append('\t\t\t\tbuilding_level >= 1')
        t.append('\t\t\t}')
        t.append('\t\t}')
    t.append('\t}\n}\n')
    t.append('# subject scope (root = the overlord): row balance_tier_row holds scope:btype')
    t.append('balance_tier_is_row_type = {\n\tOR = {')
    for n in range(1, ROWS + 1):
        t.append('\t\tAND = { root = { var:balance_tier_row = %d } var:balance_prio_%d_b ?= scope:btype }' % (n, n))
    t.append('\t}\n}')
    write('in_game/common/scripted_triggers/balance_colony_tier_triggers.txt', '\n'.join(t) + '\n')

    # ---- effects
    e = ['# THE COLONY WINDOW\'S BUILDING LEVELS (gui/balance_colony_window.gui): the popup\n# that switches a priority row to another level of its building.', HEADER]
    e.append('# root = the overlord, scope:btype = the row\'s building: every level of it, the\n# oldest first, in balance_tier_list')
    e.append('balance_tier_fill = {\n\tclear_variable_list = balance_tier_list')
    for k, chain in enumerate(chains):
        e.append('\t%s = {' % ('if' if k == 0 else 'else_if'))
        e.append('\t\tlimit = {\n\t\t\tOR = {')
        e += ['\t\t\t\tscope:btype = building_type:%s' % b for b in chain]
        e.append('\t\t\t}\n\t\t}')
        e += ['\t\tadd_to_variable_list = { name = balance_tier_list target = building_type:%s }' % b for b in chain]
        e.append('\t}')
    e.append('}\n')
    e.append('balance_tier_clear = {\n\tif = { limit = { has_variable = balance_tier_row } remove_variable = balance_tier_row }\n\tclear_variable_list = balance_tier_list\n}\n')
    e.append('# subject scope: row S now holds scope:btype. Its profit readings were for the\n# old building; "upgrades only" goes back to "everywhere" when the new one\n# replaces nothing.')
    e.append('balance_tier_set_slot = {')
    e.append('\tset_variable = { name = balance_prio_$S$_b value = scope:btype }')
    e.append('\tif = { limit = { has_variable = balance_prio_$S$_pavg } remove_variable = balance_prio_$S$_pavg }')
    e.append('\tif = { limit = { has_variable = balance_prio_$S$_pn } remove_variable = balance_prio_$S$_pn }')
    e.append('\tif = {\n\t\tlimit = {\n\t\t\tvar:balance_prio_$S$_where ?= 3\n\t\t\tNOT = { balance_prio_row_can_upgrade = { S = $S$ } }\n\t\t}\n\t\tset_variable = { name = balance_prio_$S$_where value = 0 }\n\t}')
    e.append('}\n')
    e.append('# subject scope, root = the overlord: the row the popup was opened for')
    e.append('balance_tier_set_row = {')
    for n in range(1, ROWS + 1):
        e.append('\t%s = { limit = { root = { var:balance_tier_row = %d } } balance_tier_set_slot = { S = %d } }' % ('if' if n == 1 else 'else_if', n, n))
    e.append('}')
    write('in_game/common/scripted_effects/balance_colony_tier_effects.txt', '\n'.join(e) + '\n')

    # ---- scripted guis
    g = ['# THE COLONY WINDOW\'S BUILDING LEVELS (gui/balance_colony_window.gui): click a\n# priority row\'s building to switch it to an older or newer level of it.', HEADER]
    for n in range(1, ROWS + 1):
        g.append('''balance_tier_open_{n} = {{
	scope = country
	is_valid = {{
		has_variable = balance_colony_subject
		var:balance_colony_subject ?= {{
			is_subject_of = root
			balance_tier_row_has_chain = {{ S = {n} }}
		}}
	}}
	effect = {{
		set_variable = {{ name = balance_tier_row value = {n} }}
		var:balance_colony_subject = {{
			var:balance_prio_{n}_b = {{ save_temporary_scope_as = btype }}
		}}
		balance_tier_fill = yes
	}}
}}

balance_tier_chain_{n} = {{
	scope = country
	is_shown = {{
		var:balance_colony_subject ?= {{ balance_tier_row_has_chain = {{ S = {n} }} }}
	}}
}}
'''.format(n=n))
    g.append('''# switch the open row to scope:btype: one the subject can build, not already in its list
balance_tier_pick = {
	scope = country
	saved_scopes = { btype }
	is_valid = {
		has_variable = balance_colony_subject
		has_variable = balance_tier_row
		var:balance_colony_subject ?= {
			is_subject_of = root
			can_build_building = scope:btype
			NOT = { balance_prio_has_b = yes }
		}
	}
	effect = {
		var:balance_colony_subject = {
			balance_tier_set_row = yes
			if = {
				limit = { is_target_in_variable_list = { name = balance_forbid_buildings target = scope:btype } }
				remove_list_variable = { name = balance_forbid_buildings target = scope:btype }
			}
		}
		balance_tier_clear = yes
	}
}

balance_tier_close = {
	scope = country
	effect = { balance_tier_clear = yes }
}

# the level the open row holds now
balance_tier_is_current = {
	scope = country
	saved_scopes = { btype }
	is_shown = {
		var:balance_colony_subject ?= { balance_tier_is_row_type = yes }
	}
}

# unlocked for the subject (its advances and the building's own conditions)
balance_tier_unlocked = {
	scope = country
	saved_scopes = { btype }
	is_shown = {
		var:balance_colony_subject ?= { can_build_building = scope:btype }
	}
}

# in another row of the list already
balance_tier_listed = {
	scope = country
	saved_scopes = { btype }
	is_shown = {
		var:balance_colony_subject ?= {
			balance_prio_has_b = yes
			NOT = { balance_tier_is_row_type = yes }
		}
	}
}''')
    write('in_game/common/scripted_guis/balance_colony_tier_gui.txt', '\n'.join(g) + '\n')
    print(len(chains), 'chains,', sum(len(v) for v in pred.values()), 'upgrade links')


if __name__ == '__main__':
    main()
