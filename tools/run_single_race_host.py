import os, time, subprocess, sys

PYTHON = sys.executable
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ['PYTHONPATH'] = ROOT

cmd = [PYTHON, os.path.join(ROOT, 'scripts', 'run_single_race.py'), '--venue', '浦和', '--race', '9', '--perf', '--full', '--skip-dup']
start = time.perf_counter()
with open('host_run_stdout.txt', 'w', encoding='utf-8') as out, open('host_run_stderr.txt', 'w', encoding='utf-8') as err:
    res = subprocess.run(cmd, stdout=out, stderr=err)
end = time.perf_counter()

r = {'returncode': res.returncode, 'elapsed_s': end - start}
print(r)

# print last few lines of stdout for quick info
with open('host_run_stdout.txt', 'r', encoding='utf-8', errors='replace') as out:
    lines = out.readlines()[-20:]
    print(''.join(lines))
