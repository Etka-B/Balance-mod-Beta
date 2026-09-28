"""Adds the building-level popup and the "upgrades only" Where button to the
colony window (in_game/gui/balance_colony_window.gui). Run once; it refuses to
run twice. The scripts behind it come from tools/colony_tiers.py.

  - every priority row: the building's icon and name open the level popup
    (a small upgrade mark on the icon shows the row has other levels)
  - every priority row: a fourth Where button, "Where: upgrades only"
  - the popup, over the top of the priority list: every level of the row's
    building, the ones the subject has not unlocked greyed out
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GUI = os.path.join(ROOT, 'in_game/gui/balance_colony_window.gui')
MARK = 'balance_tier_popup'
SUBJ = "GetPlayer.MakeScope.GetVariable('balance_colony_subject').GetCountry.MakeScope"


def block_end(lines, start):
    depth = 0
    for k in range(start, len(lines)):
        depth += lines[k].count('{') - lines[k].count('}')
        if depth == 0:
            return k
    raise ValueError('unclosed block at line %d' % (start + 1))


def block_start(lines, k, opener):
    while not lines[k].strip().startswith(opener):
        k -= 1
    return k


def indent(line):
    return line[:len(line) - len(line.lstrip('\t'))]


def row_opener(n, ind):
    root = "GuiScope.SetRoot(GetPlayer.MakeScope).End"
    shown = "GetScriptedGui('balance_tier_chain_%d').IsShown(%s)" % (n, root)
    return '\n'.join(ind + l for l in [
        '# the building\'s other levels (tools/colony_tier_gui_patch.py)',
        'icon = {',
        '\tvisible = "[%s]"' % shown,
        '\tposition = { 60 19 }',
        '\tsize = { 16 16 }',
        '\ttexture = "gfx/interface/icons/flat_icons/mass_upgrade.dds"',
        '}',
        'button = {',
        '\tvisible = "[%s]"' % shown,
        '\tposition = { 41 3 }',
        '\tsize = { 186 32 }',
        '\tonclick = "[GetScriptedGui(\'balance_tier_open_%d\').Execute(%s)]"' % (n, root),
        '\tonclick = "[GetVariableSystem.Set(\'%s\', \'1\')]"' % MARK,
        '}',
    ])


def popup(ind):
    root = "GuiScope.SetRoot(GetPlayer.MakeScope)"
    item = root + ".AddScope('btype', Scope.GetBuildingType.MakeScope).End"
    body = '''# the level popup: every level of the clicked row's building
# (tools/colony_tier_gui_patch.py; scripts from tools/colony_tiers.py)
widget = {
	visible = "[And(GetVariableSystem.Exists('%(mark)s'), Not(IsDataModelEmpty(GetPlayer.MakeScope.GetList('balance_tier_list'))))]"
	position = { 4 39 }
	size = { 420 396 }
	using = bg_main_inner_alt
	widget = {
		position = { 0 0 }
		size = { 420 36 }
		using = bg_card_header_
		text_single = {
			position = { 12 7 }
			size = { 360 22 }
			autoresize = no
			align = left|nobaseline
			fontsize = 16
			fontsize_min = 12
			text = "BALANCE_TIER_HEAD"
			default_format = "#yellow_titles"
		}
		button_minimize = {
			position = { 388 6 }
			size = { 24 24 }
			blockoverride "button_texture" {
				texture = "gfx/interface/buttons/flats/close_button_alt.dds"
				texture_density = 2
			}
			onclick = "[GetScriptedGui('balance_tier_close').Execute(%(root)s.End)]"
			onclick = "[GetVariableSystem.Clear('%(mark)s')]"
		}
	}
	text_multi = {
		position = { 12 40 }
		size = { 396 36 }
		autoresize = no
		fontsize = 12
		fontsize_min = 10
		text = "BALANCE_TIER_HINT"
		default_format = "#weak"
	}
	scrollarea = {
		position = { 6 80 }
		size = { 408 308 }
		scrollbarpolicy_horizontal = always_off
		scrollbar_vertical = { using = Scrollbar_Vertical }
		scrollwidget = {
			fixedgridbox = {
				addcolumn = 390
				addrow = 44
				setitemsizefromcell = yes
				datamodel = "[GetPlayer.MakeScope.GetList('balance_tier_list')]"
				item = {
					widget = {
						size = { 390 42 }
						using = bg_scroll_card
						background = {
							visible = "[GetScriptedGui('balance_tier_is_current').IsShown(%(item)s)]"
							using = color_dark_blue_texture
							alpha = 0.6
						}
						icon = {
							position = { 6 4 }
							size = { 34 34 }
							texture = "[GetBuildingIcon(Scope.GetBuildingType.Self)]"
						}
						text_single = {
							position = { 48 10 }
							size = { 200 22 }
							autoresize = no
							align = left|nobaseline
							fontsize = 14
							fontsize_min = 10
							text = "[Scope.GetBuildingType.GetNameWithNoTooltip]"
						}
						text_single = {
							visible = "[GetScriptedGui('balance_tier_is_current').IsShown(%(item)s)]"
							position = { 252 10 }
							size = { 130 22 }
							autoresize = no
							align = right|nobaseline
							fontsize = 13
							fontsize_min = 10
							text = "BALANCE_TIER_CURRENT"
						}
						text_single = {
							visible = "[GetScriptedGui('balance_tier_listed').IsShown(%(item)s)]"
							position = { 252 10 }
							size = { 130 22 }
							autoresize = no
							align = right|nobaseline
							fontsize = 13
							fontsize_min = 10
							text = "BALANCE_TIER_LISTED"
						}
						text_single = {
							visible = "[And3(Not(GetScriptedGui('balance_tier_is_current').IsShown(%(item)s)), Not(GetScriptedGui('balance_tier_listed').IsShown(%(item)s)), Not(GetScriptedGui('balance_tier_unlocked').IsShown(%(item)s)))]"
							position = { 252 10 }
							size = { 130 22 }
							autoresize = no
							align = right|nobaseline
							fontsize = 13
							fontsize_min = 10
							text = "BALANCE_TIER_LOCKED"
						}
						button_regular = {
							visible = "[GetScriptedGui('balance_tier_pick').IsValid(%(item)s)]"
							position = { 262 7 }
							size = { 120 28 }
							fontsize = 13
							fontsize_min = 10
							text = "BALANCE_TIER_SWITCH"
							onclick = "[GetScriptedGui('balance_tier_pick').Execute(%(item)s)]"
							onclick = "[GetVariableSystem.Clear('%(mark)s')]"
						}
					}
				}
			}
		}
	}
}''' % {'mark': MARK, 'root': root, 'item': item}
    return '\n'.join(ind + l if l else l for l in body.split('\n'))


def main():
    s = open(GUI, encoding='utf-8-sig').read()
    if MARK in s:
        raise SystemExit('already patched')
    L = s.split('\n')

    # rows 1..20, from the bottom up so earlier line numbers stay put
    for n in range(20, 0, -1):
        # the Where button: add "upgrades only" after "towns, cities"
        k = next(i for i, l in enumerate(L) if l.strip() == 'text = "BALANCE_PRIO_W2"'
                 and "balance_prio_%d_where'" % n in L[i - 5] + L[i - 4] + L[i - 3])
        a = block_start(L, k, 'button_regular = {')
        b = block_end(L, a)
        copy = [l.replace("'(CFixedPoint)2'", "'(CFixedPoint)3'").replace('"BALANCE_PRIO_W2"', '"BALANCE_PRIO_W3"')
                for l in L[a:b + 1]]
        L[b + 1:b + 1] = copy
        # the building's name: the level popup opens from icon and name
        k = next(i for i, l in enumerate(L)
                 if "GetVariable('balance_prio_%d_b').GetBuildingType.GetNameWithNoTooltip]" % n in l)
        a = block_start(L, k, 'text_single = {')
        b = block_end(L, a)
        L[b + 1:b + 1] = row_opener(n, indent(L[a])).split('\n')

    # the popup, drawn after (over) the priority list's scroll area
    k = next(i for i, l in enumerate(L) if l.strip() == 'size = { 747 488 }')
    a = block_start(L, k, 'scrollarea = {')
    b = block_end(L, a)
    L[b + 1:b + 1] = popup(indent(L[a])).split('\n')

    open(GUI, 'w', encoding='utf-8', newline='\n').write('\n'.join(L))
    print('patched', GUI)


if __name__ == '__main__':
    main()
