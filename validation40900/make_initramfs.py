import gzip,pathlib,stat
out=bytearray();ino=0
def add(name,mode,data=b'',major=0,minor=0):
 global ino
 ino+=1;n=name.encode()+b'\0';fields=[ino,mode,0,0,1,0,len(data),0,0,major,minor,len(n),0]
 out.extend(b'070701'+b''.join(f'{x:08x}'.encode() for x in fields)+n);out.extend(b'\0'*(-len(out)%4));out.extend(data);out.extend(b'\0'*(-len(out)%4))
for d in ['dev','proc','sys','tmp']:add(d,stat.S_IFDIR|0o755)
add('dev/console',stat.S_IFCHR|0o600,major=5,minor=1)
add('dev/null',stat.S_IFCHR|0o666,major=1,minor=3)
add('dev/ttyAMA0',stat.S_IFCHR|0o600,major=204,minor=64)
add('init',stat.S_IFREG|0o755,pathlib.Path('test-init').read_bytes())
if pathlib.Path('probe.kpm').is_file():add('probe.kpm',stat.S_IFREG|0o600,pathlib.Path('probe.kpm').read_bytes())
if pathlib.Path('test-main-init.c').is_file():
 add('data',stat.S_IFDIR|0o755)
 add('data/adb',stat.S_IFDIR|0o700)
 add('data/adb/ksud',stat.S_IFREG|0o755,pathlib.Path('test-init').read_bytes())
 add('data/adb/badksud',stat.S_IFREG|0o755,b'bad ELF fixture')
add('TRAILER!!!',0)
pathlib.Path('test-initramfs.cpio.gz').write_bytes(gzip.compress(bytes(out),mtime=0))
