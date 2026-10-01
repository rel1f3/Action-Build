"""Derive one device workflow; upstream-owned files remain byte-for-byte intact."""
import hashlib,json,pathlib,re,sys,yaml
ROOT=pathlib.Path(__file__).resolve().parents[2];P=pathlib.Path(__file__).parent
C=json.loads((P/'profile.json').read_text(encoding='utf-8'))
def ready():
 pin=C.get('manager_artifact')
 if not isinstance(pin,dict) or pin.get('verified') is not True:raise ValueError('verified signed manager artifact is not pinned')
 raw=pin.get('manifest_json','')
 if not isinstance(raw,str) or hashlib.sha256(raw.encode()).hexdigest()!=pin.get('manifest_sha256'):raise ValueError('signed manager manifest digest differs')
 m=json.loads(raw)
 expected={'manager_source_sha':C['manager_source_sha'],'manager_version_code':C['manager_version'],'manager_uapi_version':C['kernel_uapi'],'application_id':C['package'],'certificate_der_size':C['certificate_der_size'],'certificate_sha256':C['certificate_sha256'],'apk_signing_schemes':['v2'],'mode':'builtin-only','kernel_candidate_source_sha':C['builtin_sha']}
 for k,v in expected.items():
  if m.get(k)!=v:raise ValueError('signed manager identity differs: '+k)
 digest=pin.get('apk_sha256','')
 if not re.fullmatch('[0-9a-f]{64}',digest) or m.get('apk_sha256')!=digest:raise ValueError('signed manager APK digest differs')
 run=pin.get('run_id');artifact=pin.get('artifact_id')
 if type(run) is not int or run<1 or type(artifact) is not int or artifact<1:raise ValueError('missing signed manager artifact origin')
 if m.get('build_run_id')!=str(run):raise ValueError('manifest and artifact runs differ')
 if pin.get('artifact_url')!=f'https://github.com/rel1f3/SukiSU-Manager-Build/actions/runs/{run}/artifacts/{artifact}':raise ValueError('unexpected signed manager artifact origin')
 if not re.fullmatch('[0-9a-f]{40}',pin.get('workflow_commit','')):raise ValueError('manager workflow commit is not pinned')
 return m
def once(t,a,b):
 if t.count(a)!=1:raise ValueError('upstream integration anchor changed: '+a)
 return t.replace(a,b)
def generate():
 ready()
 raw=(ROOT/'.github/workflows/Build Kernel OnePlus.yml').read_text(encoding='utf-8');d=yaml.safe_load(raw)
 if True in d:d['on']=d.pop(True)
 if set(C['inputs'])!=set(d['on']['workflow_dispatch']['inputs']):raise ValueError('review upstream input changes')
 d['name']='Ace5 Pro builtin 40900';d['on']={'workflow_dispatch':None,'push':{'branches':['SukiSU-Ultra'],'paths':['custom/ace5pro/**','.github/workflows/Ace5 Pro.yml']}}
 d['permissions']={'contents':'read','actions':'read'};d['concurrency']={'group':'ace5pro-builtin-${{ github.ref }}','cancel-in-progress':False}
 steps=d['jobs']['build']['steps'];out=[]
 for step in steps:
  name=step.get('name');run=step.get('run','')
  if name=='Configure Git':run='''git config --global user.name 'github-actions[bot]'
git config --global user.email '41898282+github-actions[bot]@users.noreply.github.com'
mkdir -p kernel_workspace/Action-Build
git archive HEAD | tar -x -C kernel_workspace/Action-Build
'''
  if name=='Extract Manifest Info':run='''mkdir -p .repo/manifests_fallback
cp custom/ace5pro/manifest.xml .repo/manifests_fallback/oneplus_ace5_pro_b.xml
{ echo 'FILE=oneplus_ace5_pro_b'; echo 'FILE_CONF=oneplus_ace5_pro'; echo 'FILE_BASE=OnePlusAce5Pro'; echo 'MANIFEST_REPO=OnePlusOSS'; echo 'MANIFEST_REPO_NAME=kernel_manifest'; echo 'MANIFEST_BRANCH=oneplus/sm8750'; echo 'CPU=sm8750'; echo 'CPUD=sun'; echo 'ANDROID_VERSION=16.0.0'; echo 'ANDROID_SHORT_VERSION=16'; echo 'BUILD_METHOD=perf'; } >> "$GITHUB_ENV"
echo 'value=OnePlusAce5Pro_Android16.0.0' >> "$GITHUB_OUTPUT"
'''
  if name=='Initialize Repo and Sync':run=once(run,'repo sync -c -j$(nproc) --no-clone-bundle --no-tags --force-sync','''cp "$GITHUB_WORKSPACE/custom/ace5pro/manifest.xml" ".repo/manifests/${FILE}.xml"
repo sync -c -j$(nproc) --no-clone-bundle --no-tags --force-sync
repo manifest -r -o "$GITHUB_WORKSPACE/resolved-manifest.xml"
python3 "$GITHUB_WORKSPACE/custom/ace5pro/overlay.py" pins "$PWD"
''')
  if name=='Add SukiSU Ultra':run='''set -euo pipefail
cd kernel_workspace/kernel_platform
git clone --branch builtin https://github.com/SukiSU-Ultra/SukiSU-Ultra.git KernelSU
git -C KernelSU checkout --detach b20dee702035af09cb2ecb5f35443bbc1747f3e6
ln -s ../../KernelSU/kernel common/drivers/kernelsu
printf '\\nobj-$(CONFIG_KSU) += kernelsu/\\n' >> common/drivers/Makefile
sed -i '/endmenu/i source "drivers/kernelsu/Kconfig"' common/drivers/Kconfig
python3 "$GITHUB_WORKSPACE/custom/ace5pro/overlay.py" auth KernelSU
echo 'KSUVER=40900' >> "$GITHUB_ENV"
echo 'KSU_MANAGER_BRANCH=904c60d18f026340ce38ca2d5a1da529aadcba1a' >> "$GITHUB_ENV"
echo 'KSU_BUILTIN_BRANCH=builtin' >> "$GITHUB_ENV"
'''
  if name=='Apply Patches SukiSU Ultra':run=once(run,'git clone https://github.com/ShirkNeko/SukiSU_patch.git','git clone https://github.com/ShirkNeko/SukiSU_patch.git\ngit -C SukiSU_patch checkout --detach '+C['patch_pins']['SukiSU_patch'])
  if 'Numbersf/SCHED_PATCH' in run:
   line=next(s.strip() for s in run.splitlines() if 'git clone' in s and 'Numbersf/SCHED_PATCH' in s)
   run=once(run,line,line+'\ngit -C SCHED_PATCH checkout --detach '+C['patch_pins']['SCHED_PATCH'])
  if name=='Make AnyKernel3':run='''git clone https://github.com/Numbersf/AnyKernel3 --depth=1
git -C AnyKernel3 fetch --depth=1 origin '''+C['patch_pins']['AnyKernel3']+'''
git -C AnyKernel3 checkout --detach '''+C['patch_pins']['AnyKernel3']+'''
rm -rf AnyKernel3/.git
image=kernel_workspace/kernel_platform/out/msm-kernel-sun-perf/dist/Image
test -s "$image"
mkdir -p kernel_workspace/kernel_platform/out/Final-Image-Find
cp "$image" AnyKernel3/Image
cp "$image" kernel_workspace/kernel_platform/out/Final-Image-Find/Image
'''
  if name=='Apply KPX and Replace Image':run='''set -euo pipefail
patcher="$GITHUB_WORKSPACE/kernel_workspace/SukiSU_patch/kpm/patch_linux"
echo "'''+C['kpm_patcher_sha256']+'''  $patcher" | sha256sum -c -
cd kernel_workspace/kernel_platform/out/Final-Image-Find
cp Image raw-Image; cp "$patcher" patch_linux; chmod +x patch_linux
./patch_linux 2>&1 | tee "$GITHUB_WORKSPACE/kpm-patch.log"
test -s oImage; ! cmp -s raw-Image oImage
mv oImage Image; cp Image "$GITHUB_WORKSPACE/AnyKernel3/Image"
'''
  if name=='Download Latest SukiSU-Ultra APK from CI':continue
  if 'run' in step:step['run']=run
  if name=='Build Kernel FAST':out.append({'name':'Set verified 6.6.118 display identity','run':'python3 custom/ace5pro/overlay.py identity kernel_workspace/kernel_platform --env "$GITHUB_ENV"'})
  if name=='Upload AnyKernel3':out.append({'name':'Check packaged final Image and KPM provenance','run':'''python3 custom/ace5pro/verify.py --image AnyKernel3/Image --raw kernel_workspace/kernel_platform/out/Final-Image-Find/raw-Image --patcher kernel_workspace/SukiSU_patch/kpm/patch_linux --platform kernel_workspace/kernel_platform --out AnyKernel3/build-provenance.json
cp resolved-manifest.xml custom/ace5pro/profile.json AnyKernel3/
'''})
  out.append(step)
  if name=='Checkout':out.append({'name':'Check generated profile','run':'python3 -m pip install --disable-pip-version-check PyYAML==6.0.3\npython3 custom/ace5pro/generate.py --check'})
  if name=='Maximize Build Space':out.append({'name':'Restore independent profile after volume mount','if':step.get('if'),'uses':'actions/checkout@v7','with':{'persist-credentials':False}})
  if name=='Revert and Postfix Fake Patches':out.append({'name':'Match pinned builtin bool ABI and vendor 4K targets','run':'python3 custom/ace5pro/overlay.py abi kernel_workspace/kernel_platform --susfs kernel_workspace/susfs4ksu'})
 d['jobs']['build']['steps']=out;d['jobs']['build']['timeout-minutes']=150
 def rewrite(x):
  if isinstance(x,dict):return{k:rewrite(v) for k,v in x.items()}
  if isinstance(x,list):return[rewrite(v) for v in x]
  if not isinstance(x,str):return x
  for k,v in sorted(C['inputs'].items(),key=lambda z:-len(z[0])):
   if "'" in v or '\n' in v:raise ValueError('unsafe profile input')
   x=re.sub(r'github\.event\.inputs\.'+re.escape(k)+r'\b',lambda _:"'"+v+"'",x)
  return x
 return '# Generated from unchanged upstream '+C['upstream_commit']+'\n# Upstream workflow SHA256: '+hashlib.sha256(raw.encode()).hexdigest()+'\n'+yaml.safe_dump(rewrite(d),sort_keys=False,width=130,allow_unicode=True)
if __name__=='__main__':
 path=ROOT/'.github/workflows/Ace5 Pro.yml';text=generate()
 if '--check' in sys.argv:
  if path.read_text(encoding='utf-8')!=text:raise SystemExit('regenerate/review device workflow')
 else:path.write_text(text,encoding='utf-8',newline='\n')
