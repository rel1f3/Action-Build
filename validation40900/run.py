import hashlib,json,pathlib,subprocess,zipfile,re
out=pathlib.Path('test-results');out.mkdir(exist_ok=True)
files=list(pathlib.Path('artifact').rglob('Image'))
if not files:
 for archive in pathlib.Path('artifact').rglob('*.zip'):
  with zipfile.ZipFile(archive) as z:
   if 'Image' in z.namelist():z.extractall('artifact/unpacked')
 files=list(pathlib.Path('artifact').rglob('Image'))
if len(files)!=1:raise SystemExit('expected exactly one packaged Image')
image=files[0];provenance=json.loads(image.with_name('build-provenance.json').read_text())
digest=hashlib.sha256(image.read_bytes()).hexdigest()
if digest!=provenance['image_sha256'] or digest==provenance['raw_image_sha256'] or not provenance['kpm_image_changed']:raise SystemExit('final KPM Image differs from provenance')
if provenance['kernel_uapi']!=2 or provenance['driver_build_id']!=40900 or provenance['builtin_sha']!='b20dee702035af09cb2ecb5f35443bbc1747f3e6':raise SystemExit('incorrect pairing provenance')
(out/'build-provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
results=[]
for attempt,(cpus,seconds) in enumerate(((1,30),(4,60),(8,60),(4,30)),1):
 cmd=['qemu-system-aarch64','-machine','virt,gic-version=3','-cpu','max','-accel','tcg','-smp',str(cpus),'-m','2048','-nographic','-nic','none','-monitor','none','-no-reboot','-kernel',str(image),'-initrd','test-initramfs.cpio.gz','-append','console=ttyAMA0 earlycon=pl011,0x09000000 rdinit=/init nokaslr panic=-1 KTEST_SECONDS='+str(seconds)]
 try:p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=seconds+180);log=p.stdout;code=p.returncode
 except subprocess.TimeoutExpired as e:log=e.stdout or b'';code=124
 (out/f'qemu-final-{attempt}-smp{cpus}.log').write_bytes(log)
 required=[b'TEST_PASS:',b'KSU_RUNTIME_PASS',b'KSU_PERMISSION_PASS',b'KPM_RUNTIME_PASS',b'KPM_PERMISSION_PASS',b'SELINUX_HIDE_DEFAULT_PASS',b'STRESS_ALL_PASS',b'KSU_INFO version=40900 flags=0 features=5 uapi=2',f'ONLINE_CPUS={cpus}'.encode()]+[f'STRESS_CPU_PASS cpu={i} '.encode() for i in range(cpus)]
 forbidden=[b'TEST_FAIL:',b'Kernel panic',b'Internal error:',b'Oops:',b'BUG:',b'WARNING:',b'Stub function called']
 passed=code==0 and all(s in log for s in required) and not any(s in log for s in forbidden)
 full_matches=re.findall(rb'KSU_FULL_VERSION=([^\r\n]+)',log)
 native_full=full_matches[0].decode('ascii') if len(full_matches)==1 else ''
 info_matches=re.findall(rb'KSU_INFO version=(\d+) flags=(\d+) features=(\d+) uapi=(\d+)',log)
 observed_version=int(info_matches[0][0]) if len(info_matches)==1 else None
 observed_uapi=int(info_matches[0][3]) if len(info_matches)==1 else None
 gate_passed=False
 if native_full and native_full==provenance['kernel_full_version'] and observed_version is not None and observed_uapi is not None:
  gate=subprocess.run(['java','-jar','exact-manager-gate.jar',native_full,str(observed_version),str(observed_uapi)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  (out/f'exact-manager-gate-{attempt}.log').write_bytes(gate.stdout);print(gate.stdout.decode(errors='replace'))
  gate_passed=gate.returncode==0 and b'EXACT_MANAGER_GATE_PASS' in gate.stdout
 passed=passed and gate_passed
 results.append(dict(observed_driver_version=observed_version,observed_kernel_uapi=observed_uapi,native_full_version=native_full,manager_version_gate_passed=gate_passed,attempt=attempt,cpus=cpus,stress_seconds=seconds,exit_code=code,passed=passed,command=cmd));print(log.decode(errors='replace')[-12000:])
report=dict(build_run_id=36849458473,image_sha256=digest,image_modified=False,kernel_uapi=results[0]['observed_kernel_uapi'],driver_version=results[0]['observed_driver_version'],builtin_sha=provenance['builtin_sha'],final_kpm_image=True,tests=results,driver_runtime_verified=all(r['passed'] for r in results),manager_version_gate_verified=all(r['manager_version_gate_passed'] for r in results),qemu_passed=all(r['passed'] for r in results),device_boot_tested=False,display_tested=False,vendor_module_abi_tested=False,android_framework_tested=False,manager_root_authorization_tested=False,unsupported_builtin_ioctl=[104,105],selinux_hide_changed=False)
(out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if not report['qemu_passed']:raise SystemExit('builtin UAPI2/final KPM runtime validation failed; inspect logs')
