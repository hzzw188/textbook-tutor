"""Resolve a Bilibili part and pass it to the separately installed transcript tool."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.error import URLError
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

DEFAULT_TOOL = Path.home() / 'bilibili-transcript'


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description='Extract one accessible Bilibili lesson using the separately installed transcript tool.')
    parser.add_argument('url')
    parser.add_argument('--tool-dir', type=Path, default=DEFAULT_TOOL,
                        help='transcript tool directory (default: ~/bilibili-transcript)')
    parser.add_argument('--model', default='base')
    args = parser.parse_args()
    url = urlparse(args.url)
    match = re.fullmatch(r'/video/(BV[0-9A-Za-z]+)/*', url.path)
    if url.scheme not in ('http', 'https') or url.hostname not in ('www.bilibili.com', 'bilibili.com') or not match:
        parser.error('Expected a bilibili.com/video/BV... URL')
    pages = parse_qs(url.query).get('p', ['1'])
    if len(pages) != 1 or not pages[0].isdigit() or int(pages[0]) < 1:
        parser.error('Invalid part number')
    bvid, part_number = match.group(1), int(pages[0])
    tool = args.tool_dir.expanduser().resolve()
    output = tool / 'output' / f'{bvid}_p{part_number}.doc.md'
    if output.is_file():
        print(f'Existing transcript (not regenerated): {output}', flush=True)
        return

    venv_python = 'Scripts/python.exe' if os.name == 'nt' else 'bin/python'
    python = tool / '.venv312' / venv_python
    runner = tool / 'workflow' / 'bili_to_doc.py'
    if not python.is_file() or not runner.is_file():
        parser.error('Transcript tool or its .venv312 environment is missing. '
                     'See README.md for setup or supply --tool-dir.')

    request = Request(f'https://api.bilibili.com/x/web-interface/view?bvid={bvid}', headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urlopen(request, timeout=20) as response:
            data = json.load(response)
    except URLError:
        parser.exit(1, 'Could not reach the Bilibili metadata API. Check your network or provide an existing transcript.\n')
    if data.get('code') != 0:
        raise RuntimeError(f"Bilibili metadata error: {data.get('message', data.get('code'))}")
    parts = data['data']['pages']
    if part_number > len(parts):
        parser.error(f'Part {part_number} does not exist; course has {len(parts)} parts')
    part = parts[part_number - 1]
    duration = int(part['duration'])
    if duration <= 0:
        raise ValueError('Part duration is missing')
    if output.with_suffix('.html').exists():
        raise FileExistsError('HTML output already exists; choose another output location')
    end = f'{duration // 3600:02d}:{duration % 3600 // 60:02d}:{duration % 60:02d}'
    print(f"Part {part_number}: {part['part']} ({end})", flush=True)
    env = os.environ.copy()
    env.pop('BILI_SESSDATA', None)
    env['HF_HOME'] = str(tool / 'model-cache')
    env['HF_HUB_DISABLE_XET'] = '1'
    subprocess.run([str(python), str(runner), f'https://www.bilibili.com/video/{bvid}/?p={part_number}',
                    '--page', str(part_number), '--start', '00:00', '--end', end,
                    '--no-cookies', '--model', args.model, '--device', 'cpu', '--name', f'{bvid}_p{part_number}'],
                   cwd=tool, env=env, check=True)
    if not output.is_file():
        raise RuntimeError(f'Transcript tool finished but output was not found: {output}')
    print(f'Transcript: {output}', flush=True)


if __name__ == '__main__':
    main()
