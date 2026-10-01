"""Small, pinned device overlay; the maintained builtin supplies SUSFS itself."""
import argparse,datetime,json,pathlib,re,subprocess
P=pathlib.Path(__file__).with_name('profile.json')
C=json.loads(P.read_text(encoding='utf-8'))
def head(p):return subprocess.check_output(['git','-C',str(p),'rev-parse','HEAD'],text=True).strip()
def replace(t,a,b):
 if t.count(a)!=1:raise ValueError('unreviewed integration anchor: '+a[:100])
 return t.replace(a,b)
def auth(root):
 if head(root)!=C['builtin_sha']:raise ValueError('unreviewed builtin')
 uapi=(root/'kernel/include/uapi/supercall.h').read_text(encoding='utf-8')
 if not re.search(r'DECLARE\(__u32,\s*KERNEL_SU_UAPI_VERSION,\s*2\)',uapi):raise ValueError('builtin is not native UAPI2')
 sign=root/'kernel/manager/apk_sign.c';t=sign.read_text(encoding='utf-8')
 pattern=r'(static struct apk_sign_key\s*\{[^}]+\}\s*apk_sign_keys\[\]\s*=\s*\{).*?(\n\};)'
 t,n=re.subn(pattern,lambda m:m[1]+'\n    { '+str(C['certificate_der_size'])+', "'+C['certificate_sha256']+'" }, // private manager\n'+m[2],t,flags=re.S)
 if n!=1 or 'KSU_MANAGER_PACKAGE' not in t:raise ValueError('unreviewed authentication parser')
 sign.write_text(t,encoding='utf-8',newline='\n')
 make=root/'kernel/Makefile';t=make.read_text(encoding='utf-8')
 t=replace(t,'KSU_VERSION     := $(if $(LOCAL_COUNT),$(shell expr $(VERSION_BASE) + $(LOCAL_COUNT) - $(VERSION_OFFSET)),13000)','KSU_VERSION     := '+str(C['driver_build_id']))
 if t.count('ifdef KSU_MANAGER_PACKAGE')!=1:raise ValueError('package overlay anchor changed')
 make.write_text('KSU_MANAGER_PACKAGE := '+C['package']+'\n'+t,encoding='utf-8',newline='\n')
 print('Custom pairing build ID:',C['driver_build_id'],'actual source:',C['builtin_sha'])
def abi(platform,susfs):
 if head(platform/'KernelSU')!=C['builtin_sha'] or head(susfs)!=C['inputs']['SUSFS_META']:raise ValueError('unreviewed SUSFS/builtin pair')
 source=(platform/'KernelSU/kernel/feature/sucompat.c').read_text(encoding='utf-8')
 if 'bool ksu_su_compat_enabled __read_mostly = true;' not in source or 'ksu_handle_post_execveat_sucompat' in source:raise ValueError('unexpected builtin hook ABI')
 patch=(susfs/'kernel_patches/50_add_susfs_in_gki-android15-6.6.patch').read_text(encoding='utf-8')
 if 'ksu_handle_post_execveat_sucompat' in patch:raise ValueError('scoped/post-exec protocol requires a different driver')
 for name in ('fs/exec.c','fs/open.c','fs/stat.c'):
  p=platform/'common'/name;t=p.read_text(encoding='utf-8')
  t=replace(t,'extern struct static_key_true ksu_su_compat_enabled;','extern bool ksu_su_compat_enabled;')
  t=replace(t,'static_branch_likely(&ksu_su_compat_enabled)','likely(READ_ONCE(ksu_su_compat_enabled))')
  p.write_text(t,encoding='utf-8',newline='\n')
 p=platform/'build_with_bazel.py';t=p.read_text(encoding='utf-8')
 line='                label_list = [l.decode("utf-8") for l in query_cmd.stdout.read().splitlines()]'
 t=replace(t,line,line+'\n                wanted = {"//msm-kernel:sun_perf_dist", "//msm-kernel:sun_perf_dtc_dist"}\n                if t != "sun" or v != "perf" or not wanted.issubset(set(label_list)):\n                    raise RuntimeError("Pinned vendor 4K targets changed")\n                label_list = [label for label in label_list if label in wanted]')
 p.write_text(t,encoding='utf-8',newline='\n')
 print('Only three bool gate consumers adapted; original vendor query retained')
def identity(platform):
 for folder in ('common','msm-kernel'):
  root=platform/folder;t=(root/'Makefile').read_text(encoding='utf-8')
  actual='.'.join(re.findall(r'^'+k+r'\s*=\s*(\d+)\s*$',t,re.M)[0] for k in ('VERSION','PATCHLEVEL','SUBLEVEL'))
  if actual!=C['kernel_version']:raise ValueError('actual source is not '+C['kernel_version'])
  p=root/'scripts/setlocalversion';old=p.read_text(encoding='utf-8')
  if 'echo "${KERNELVERSION}${file_localversion}${config_localversion}${LOCALVERSION}${scm_version}"' in old:label=C['kernel_release']
  elif 'echo "$res"' in old:label=C['kernel_release'][len(actual):]
  else:raise ValueError('setlocalversion anchor changed')
  p.write_text('#!/bin/sh\nif [ "${KERNELVERSION:-}" != "99.99.99" ]; then\n printf \'%s\\n\' '+repr(label)+'\n exit 0\nfi\n'+old,encoding='utf-8',newline='\n');p.chmod(0o755)
 epoch=int(datetime.datetime.strptime(C['build_timestamp'],'%a %b %d %H:%M:%S UTC %Y').replace(tzinfo=datetime.timezone.utc).timestamp())
 with open(a.env,'a',encoding='utf-8') as f:f.write('KBUILD_BUILD_TIMESTAMP='+C['build_timestamp']+'\nKBUILD_BUILD_VERSION=1\nSOURCE_DATE_EPOCH='+str(epoch)+'\n')
def pins(root):
 for path,sha in C['source_pins'].items():
  if head(root/path)!=sha:raise ValueError('vendor source pin changed: '+path)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['auth','abi','identity','pins']);p.add_argument('root');p.add_argument('--susfs');p.add_argument('--env');a=p.parse_args();root=pathlib.Path(a.root)
 if a.phase=='abi':abi(root,pathlib.Path(a.susfs))
 else:globals()[a.phase](root)
