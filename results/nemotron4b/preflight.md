PASS  nvidia-smi responds  
PASS  docker image present  
PASS  free disk >= 40 GiB  161 GiB
PASS  known-good scene passes  reward=1.00 err=''
PASS  infinite loop times out  'timeout'
PASS  no container left behind  
PASS  network connection fails       ~~~~~~~~~~~~^^^^ OSError: [Errno 101] Network is unreachable  Error: script failed, file: '/job/agent.py', exiting.
PASS  write_outside_job fails  ^^^^^ OSError: [Errno 30] Read-only file system: '/opt/pwned.txt'  Error: script failed, file: '/job/agent.py', exiting.
PASS  write_host_home fails  rror: [Errno 2] No such file or directory: '~/pwned.txt'  Error: script failed, file: '/job/agent.py', exiting.
PASS  host home untouched  
PASS  pre-written state.json + early exit earns nothing  reward=0.0
PASS  fork bomb contained  
