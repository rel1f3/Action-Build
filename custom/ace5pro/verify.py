"""Check packaged post-KPM Image, actual config, identity and provenance."""
import argparse,hashlib,json,pathlib,re,subprocess
C=json.loads(pathlib.Path(__file__).with_name('profile.json').read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--image',required=True);p.add_argument('--raw',required=True);p.add_argument('--patcher',required=True);p.add_argument('--platform',required=True);p.add_argument('--out',required=True);a=p.parse_args()
 image=pathlib.Path(a.image);data=image.read_bytes();platform=pathlib.Path(a.platform)
 if data[56:60]!=b'ARMd' or ((int.from_bytes(data[24:32],'little')>>1)&3)!=1:raise SystemExit('final Image is not ARM64 4K')
 banners=set(re.findall(rb'Linux version [^\x00\n]{1,1024}',data))
 if len(banners)!=1:raise SystemExit('missing unique banner')
 banner=next(iter(banners)).decode('ascii')
 if not banner.startswith('Linux version '+C['kernel_release']+' ') or C['uts_version'] not in banner:raise SystemExit('final banner differs')
 for identity in (C['package'],C['certificate_sha256'],C['builtin_sha']):
  if identity.encode() not in data:raise SystemExit('missing compiled identity '+identity)
 raw_sha=sha(a.raw);final_sha=sha(image)
 if raw_sha==final_sha or sha(a.patcher)!=C['kpm_patcher_sha256']:raise SystemExit('KPM processing provenance mismatch')
 config=subprocess.check_output(['bash',str(platform/'common/scripts/extract-ikconfig'),str(image)]).decode()
 for line in ('CONFIG_KSU=y','CONFIG_KPM=y','CONFIG_KSU_SUSFS=y','CONFIG_ARM64_4K_PAGES=y'):
  if line not in config.splitlines():raise SystemExit('missing '+line)
 if any(x in config.splitlines() for x in ('CONFIG_KSU_DEBUG=y','CONFIG_KSU_DISABLE_MANAGER=y','CONFIG_KSU_DISABLE_POLICY=y')):raise SystemExit('authentication/policy debug bypass enabled')
 image.with_name('kernel.config').write_text(config,encoding='utf-8')
 # Save compiler-generated command evidence when retained by this Kleaf version.
 evidence=[]
 for cmd in platform.rglob('*.cmd'):
  try:t=cmd.read_text(errors='replace')
  except OSError:continue
  if '-DKSU_VERSION=40900' in t and '-DKSU_VERSION_FULL=' in t:evidence.append(str(cmd))
 report=dict(source_pins=C['source_pins'],builtin_sha=C['builtin_sha'],manager_source_sha=C['manager_source_sha'],manager_manifest_sha256=C['manager_artifact']['manifest_sha256'],manager_apk_sha256=C['manager_artifact']['apk_sha256'],manager_artifact_url=C['manager_artifact']['artifact_url'],kernel_uapi=2,driver_build_id=40900,driver_build_id_is_custom=True,banner=banner,image_sha256=final_sha,raw_image_sha256=raw_sha,kpm_patcher_sha256=sha(a.patcher),kpm_image_changed=True,compiler_command_files=evidence,compiled_identity_verified=True,kpm_runtime_verified=False,device_tested=False,android_root_authorization_tested=False,unsupported_builtin_ioctl=[104,105])
 pathlib.Path(a.out).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
