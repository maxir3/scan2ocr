"""Plumbing for the scan2file test suite.

Two ways to drive the script:

  run_pipe()  feeds keystrokes through a pipe. Fast, but stdin is not a
              terminal, so the script takes its line-input fallbacks.
  run_pty()   runs it inside a real pseudo terminal and answers the
              terminal capability query the way a real terminal would.
              This is the only way to exercise raw-mode key reading,
              isatty() branches and the graphics protocol probe.

Both are needed: bugs have hidden in the tty-only paths that pipe tests
cannot reach by construction.
"""

import fcntl
import os
import pty
import select
import shutil
import struct
import subprocess
import sys
import termios
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SCRIPT = os.path.join(REPO, 'scan2file')
FAKEBIN = os.path.join(HERE, 'fakebin')

# Alacritty's answer to a Primary Device Attributes request: no sixel (that
# would need attribute 4), which is what makes it a good default to test with.
DA1_NO_GRAPHICS = b'\x1b[?6c'
DA1_SIXEL = b'\x1b[?62;4c'


def build_pages(directory, count=16):
	"""Renders numbered test pages plus one blank sheet."""
	os.makedirs(directory, exist_ok=True)
	if os.path.exists(os.path.join(directory, 'p%d.pnm' % count)):
		return directory

	for i in range(1, count + 1):
		subprocess.run([
			'magick', '-size', '620x877', 'xc:white', '-fill', 'black',
			'-pointsize', '90', '-annotate', '+60+200', 'SEITE %d' % i,
			'-pointsize', '40', '-annotate', '+60+320', 'Inhalt der Seite %d' % i,
			'-draw', 'rectangle 60,400 560,410',
			os.path.join(directory, 'p%d.pnm' % i),
		], check=True)

	blank = os.path.join(directory, 'blank')
	os.makedirs(blank, exist_ok=True)
	subprocess.run(['magick', '-size', '620x877', 'xc:white',
	                os.path.join(blank, 'p1.pnm')], check=True)
	shutil.copy(os.path.join(directory, 'p2.pnm'), os.path.join(blank, 'p2.pnm'))
	return directory


def make_env(workdir, pages_dir, fail_on=None, feh_log=None, extra=None):
	env = dict(os.environ)
	env['PATH'] = FAKEBIN + os.pathsep + env.get('PATH', '')
	env['FAKE_SCAN_DIR'] = pages_dir
	env['FAKE_SCAN_COUNTER'] = os.path.join(workdir, 'counter')
	env['COLUMNS'] = '132'
	env['LINES'] = '44'
	env.pop('FAKE_SCAN_FAIL', None)
	if fail_on:
		env['FAKE_SCAN_FAIL'] = str(fail_on)
	if feh_log:
		env['FEH_LOG'] = feh_log
	if extra:
		env.update(extra)
	# Start each scenario at page 1
	with open(env['FAKE_SCAN_COUNTER'], 'w') as fh:
		fh.write('0')
	return env


def run_pipe(args, keys, workdir, env, timeout=120):
	"""Drives scan2file over pipes. keys is a list of strings, one per prompt."""
	stdin = ''.join(k + '\n' for k in keys)
	p = subprocess.run([SCRIPT] + args, input=stdin, cwd=workdir, env=env,
	                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
	                   text=True, timeout=timeout)
	return (p.stdout, p.returncode)


def run_pty(args, keys, workdir, env, timeout=120, da1=DA1_NO_GRAPHICS,
            term='alacritty', preload=False, burst_after=None,
            burst_delay=0.5, key_delay=0.0):
	"""Drives scan2file inside a real pty. keys is a list of byte strings sent
	one at a time whenever the script goes quiet.

	Two type-ahead variants, which exercise different code:

	preload=True writes every key before the script draws anything. Those keys
	are still in the buffer when the terminal capability probe runs, so they
	end up in the script's own pending-input buffer.

	burst_after=N sends N keys normally and then dumps the rest at once, so
	they arrive while the script is busy scanning -- after the probe, before
	the next prompt. This is the case that a terminal flush would swallow.

	key_delay pauses before each key. Scenarios that assert a stub subprocess
	got as far as writing its log need it: otherwise the script may terminate
	the stub before the shell in it has run a single line."""
	master, slave = pty.openpty()
	fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH', 44, 132, 0, 0))

	env = dict(env)
	env['TERM'] = term

	proc = subprocess.Popen([SCRIPT] + args, stdin=slave, stdout=slave,
	                        stderr=slave, cwd=workdir, env=env, close_fds=True)
	os.close(slave)

	out = b''
	pending = list(keys)
	if preload:
		for key in pending:
			os.write(master, key)
		pending = []
	sent = 0
	deadline = time.time() + timeout
	try:
		while time.time() < deadline:
			ready, _, _ = select.select([master], [], [], 0.2)
			if ready:
				try:
					chunk = os.read(master, 65536)
				except OSError:
					break
				if not chunk:
					break
				out += chunk
				if b'\x1b[c' in chunk:	# device attributes request
					os.write(master, da1)
				continue
			if pending:
				if key_delay:
					time.sleep(key_delay)
				os.write(master, pending.pop(0))
				sent += 1
				if burst_after is not None and sent >= burst_after:
					# Wait until the script has moved on and is busy scanning,
					# so the keys land while nothing is reading them.
					time.sleep(burst_delay)
					for key in pending:
						os.write(master, key)
					pending = []
				time.sleep(0.15)
			elif proc.poll() is not None:
				break
	finally:
		try:
			proc.wait(timeout=5)
		except subprocess.TimeoutExpired:
			proc.kill()
			proc.wait(timeout=5)
		os.close(master)

	return (out.decode('utf-8', errors='replace'), proc.returncode)
