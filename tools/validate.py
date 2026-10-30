# Author: GPT-6.1 Sol
# Date: 29-October-2026
# PURPOSE: Verify release file integrity and exercise real engine resets and actions.
# SRP/DRY check: Pass — catalog and runtime are reused; no duplicate game rules.
from __future__ import annotations

import hashlib
import json
from runtime import CATALOG, ROOT, frame_record, load_game, perform


def main():
    failures = []
    for entry in CATALOG['games']:
        try:
            assert hashlib.sha256((ROOT / entry['path']).read_bytes()).hexdigest() == entry['sha256'], 'source hash mismatch'
            if entry['preview']:
                assert (ROOT / 'docs' / entry['preview']).is_file(), 'missing preview'
            game = load_game(entry['id'])
            frame = perform(game, 0)
            observation = frame_record(frame)
            assert observation['frames'], 'reset returned no frames'
            actions = [int(item) for item in frame.available_actions if int(item) != 0]
            assert actions, 'no available action'
            frame_record(perform(game, actions[0]))
            print(f"PASS {entry['id']}: reset and action")
        except Exception as exc:
            failures.append({'id': entry['id'], 'error': str(exc)})
            print(f"FAIL {entry['id']}: {exc}")
    for entry in CATALOG['support_files']:
        assert hashlib.sha256((ROOT / entry['path']).read_bytes()).hexdigest() == entry['sha256']
    report = {'checked': len(CATALOG['games']), 'failures': failures,
              'scope': 'File hashes, preview presence, module import, real engine RESET and one advertised action. Not a solvability or full-game test.'}
    (ROOT / 'docs/validation.json').write_text(json.dumps(report, indent=2) + '\n')
    raise SystemExit(bool(failures))


if __name__ == '__main__':
    main()
