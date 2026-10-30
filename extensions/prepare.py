# Author: GPT-6.1 Sol
# Date: 29-October-2026
# PURPOSE: Extract documented standalone V-series mechanic extensions and source provenance
# into this isolated release subtree, and replay existing winning lines using ARCEngine.
# Dependencies: Python 3.13, NumPy, ARCEngine; canonical game and trace files remain untouched.
# SRP/DRY check: Pass — reuses existing single-file builds and recorded solutions, no new game logic.
from pathlib import Path
import ast
import hashlib
import importlib.metadata
import json
import shutil
from arcengine import ARCBaseGame, ActionInput, GameAction, GameState

ROOT = Path(__file__).resolve().parent
SOURCE = Path('/Users/macmini/GitHub/autoresearch-arena/arc3games/polish')
# These descriptions are researcher annotations, never injected into game observations.
SPECS = [
 ('vj11','vj11','lp85','vj01','quarter turn clockwise',2,'rule_extension','Arrow-controlled walker must ride tracks and reach its own goal; track cells cannot be walked along.'),
 ('vj13','vj13','lp85','vj03','half turn',3,'topology_extension','Junction cells transfer pieces between rings; uses existing movement rules, not a new engine rule. Revised third level crosses two junctions.'),
 ('vj15','vj15','lp85','vj05','mirror left-right',2,'rule_extension','Global turn moves every track; buttonless tracks require it while other tracks must be repaired.'),
 ('vj17','vj17','lp85','vj07','mirror diagonal',2,'rule_extension','Visible spinner buttons cycle through one, two and three-cell moves; final level requires spinners.'),
 ('vz11','vz11','sp80','vz01','quarter turn',1,'rule_extension','A striped current pushes falling paint sideways.'),
 ('vz13','vz13','sp80','vz03','half turn',1,'rule_extension','Paired portals transfer paint between ring mouths. Historical version; later replaced by pf21 pipe remake.'),
 ('vz15','vz15-next2','sp80','vz05','mirror left-right',1,'rule_extension','Dye patch changes paint colour; cups require the matching paint. Uses later failure-feedback repair.'),
 ('vz17','vz17','sp80','vz07','mirror diagonal',1,'rule_extension','Current direction changes after each move; spill timing changes the paint route.'),
 ('ve13','ve13','cn04','vc13 / ve03 lineage','half turn',1,'rule_extension','Crossing a mirror stamp flips held pieces; each generated level needs a mirrored fit.'),
 ('ve15','ve15','cn04','vc15 / ve05 lineage','mirror left-right',1,'rule_extension','Unheld pieces drift with wind; dropping a piece carries it to the windward destination wall.'),
 ('vp15','vp15','ls20','vp05','mirror left-right',1,'rule_extension','Arrow actions slide until an obstacle, applying every changer crossed; uses later dead-end repair.'),
 ('vh17','vh17','ft09','vh07','mirror diagonal',1,'rule_extension','Only the selected panel accepts clicks; arrow actions select the active panel.'),
]

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def replay(path, trace):
    namespace = {'__name__': 'release_' + path.stem}
    exec(compile(path.read_text(), str(path), 'exec'), namespace)
    classes = [v for v in namespace.values() if isinstance(v,type) and issubclass(v,ARCBaseGame) and v is not ARCBaseGame]
    assert len(classes) == 1
    game = classes[0]()
    result = game.perform_action(ActionInput(id=GameAction.RESET), raw=True)
    counts = []
    for index, level in enumerate(trace['levels']):
        actions = level['actions']
        for pos, raw in enumerate(actions):
            aid, data = (raw[0], {'x':raw[1], 'y':raw[2]}) if isinstance(raw,list) else (raw,{})
            result = game.perform_action(ActionInput(id=GameAction.from_id(aid),data=data),raw=True)
            assert result.frame and all(f.shape == (64,64) and f.min() >= 0 and f.max() <= 15 for f in result.frame)
            assert game._state != GameState.GAME_OVER, (index+1,pos+1,'GAME_OVER')
            if game._score > index:
                assert pos == len(actions)-1, ('early level clear',index+1,pos+1)
        assert game._score == index+1, ('uncleared', index+1,game._score)
        counts.append(len(actions))
    assert game._state == GameState.WIN
    return {'won':True,'levels_cleared':int(game._score),'action_counts':counts,'frames':'all action frames 64x64, palette 0..15','class_name':classes[0].__name__}

entries=[]
for gid, folder, parent, control, view, introduced, kind, mechanic in SPECS:
    src=SOURCE/folder/f'{gid}.py'
    text=src.read_text()
    assert 'MIT License' in text and 'ARC Prize Foundation' in text
    assert parent not in {'vc33','ar25','sb26','re86','su15','tr87','tu93','as66'}
    imports=[]
    for node in ast.walk(ast.parse(text)):
        if isinstance(node,ast.Import): imports += [n.name for n in node.names]
        elif isinstance(node,ast.ImportFrom): imports.append(node.module)
    out=ROOT/'games'/gid
    out.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(src,out/f'{gid}.py')
    research=ROOT/'research'/gid
    research.mkdir(parents=True,exist_ok=True)
    for name in [f'{gid}.trace.json',f'{gid}.vet.json','design.md']:
        if (src.parent/name).exists(): shutil.copyfile(src.parent/name,research/name)
    trace=json.loads((research/f'{gid}.trace.json').read_text())
    try: verification=replay(out/f'{gid}.py',trace)
    except Exception as error: verification={'won':False,'error':repr(error)}
    oldvet=json.loads((research/f'{gid}.vet.json').read_text())
    entries.append({'id':gid,'title':gid,'runtime':f'games/{gid}/{gid}.py','parent_public_game':parent,'control_ancestor':control,'presentation_transform':view,'mechanic_first_level':introduced,'extension_kind':kind,'mechanic':mechanic,'historical_superseded':gid=='vz13','source_path':str(src.relative_to(SOURCE.parent.parent)),'source_sha256':digest(src),'imports':sorted(set(imports)),'license':'MIT; embedded ARC Prize Foundation notice preserved','verification':verification,'previous_vet_source_matches':oldvet.get('source_sha256')==digest(src),'evidence':f'research/{gid}/design.md'})
    print(gid,json.dumps(verification),flush=True)
manifest={'format':'arc3-mechanic-extensions/1','prepared_at':'2026-10-29 America/New_York','dependencies':{'python':'3.13','arcengine':importlib.metadata.version('arcengine'),'numpy':importlib.metadata.version('numpy')},'notes':['Research metadata contains mechanic spoilers; keep it out of evaluator observations.','Local snapshots, not a fresh upstream fetch or live-site verification.','Winning-trace replay is not a human Trainable verdict, difficulty proof or harness score improvement.','Source bytes retain original authors and full embedded MIT notices.','Pure cosmetic variants omitted. vj13 is a topology extension under existing rules.','vz13 is a historical rotated portal version replaced later by the unrotated pf21 pipe remake; do not silently call it the latest version.'],'games':entries}
(ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(ROOT/'verification.json').write_text(json.dumps({e['id']:e['verification'] for e in entries},indent=2)+'\n')
