#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <sys/mount.h>
#include <sys/stat.h>
#include <sys/utsname.h>
#include <sys/wait.h>
#include <sys/reboot.h>
#include <sys/mman.h>
#include <sched.h>
#include <time.h>
#include <sys/ioctl.h>
#include <sys/syscall.h>
#include <stdint.h>
#include <grp.h>
static void die(const char *s) { printf("TEST_FAIL: %s errno=%d\n",s,errno); fflush(stdout); for (;;) sleep(60); }
struct ksu_info { uint32_t version, flags, features, uapi_version; };
struct ksu_feature { uint32_t feature_id; uint64_t value; uint8_t supported; };
_Static_assert(sizeof(struct ksu_info)==16,"info ABI");
_Static_assert(sizeof(struct ksu_feature)==24,"feature ABI");

struct kpm_cmd { uint64_t control_code, arg1, arg2, result_code; };
_Static_assert(sizeof(struct kpm_cmd)==32,"KPM ABI");
static int kpm_call(int fd, unsigned code, void *arg1, uintptr_t arg2) {
 int result=-123456;
 struct kpm_cmd cmd={code,(uintptr_t)arg1,arg2,(uintptr_t)&result};
 if(ioctl(fd,0xc0004bc8UL,&cmd))die("KPM ioctl transport");
 printf("KPM_RESULT code=%u result=%d\n",code,result);
 return result;
}
static void probe_kpm(int fd) {
 unsigned char enabled=0;
 if(ioctl(fd,0x80004b66UL,&enabled)||enabled!=1)die("KPM config query");
 char version[256]={0},list[1024]={0},info[256]={0};
 if(kpm_call(fd,7,version,sizeof(version))||!version[0])die("KPM injected version missing");
 printf("KPM_VERSION=%s\n",version);
 int baseline=kpm_call(fd,3,NULL,0);if(baseline<0)die("KPM module count");
 if(kpm_call(fd,1,"/probe.kpm",(uintptr_t)"ci"))die("KPM load");
 if(kpm_call(fd,3,NULL,0)!=baseline+1)die("KPM count after load");
 if(kpm_call(fd,4,list,sizeof(list))<0||!strstr(list,"ace5pro-ci-probe"))die("KPM list");
 if(kpm_call(fd,5,"ace5pro-ci-probe",(uintptr_t)info)||!strstr(info,"ace5pro-ci-probe"))die("KPM short metadata info");
 if(kpm_call(fd,6,"ace5pro-ci-probe",(uintptr_t)"ci")!=73)die("KPM loaded code control result");
 if(kpm_call(fd,2,"ace5pro-ci-probe",0))die("KPM unload");
 if(kpm_call(fd,3,NULL,0)!=baseline)die("KPM count after unload");
 puts("KPM_RUNTIME_PASS: injected version load count list short info control73 unload");
}

static void probe_ksu(void) {
 int fd=-1;errno=0;long ret=syscall(SYS_reboot,0xDEADBEEFUL,0xCAFEBABEUL,0,&fd);
 printf("KSU_FD syscall_result=%ld errno=%d fd=%d\n",ret,errno,fd);
 if(fd<0)die("SukiSU fd installation");
 if(!(fcntl(fd,F_GETFD)&FD_CLOEXEC))die("SukiSU fd CLOEXEC");
 char linkpath[64],target[128]={0};snprintf(linkpath,sizeof(linkpath),"/proc/self/fd/%d",fd);ssize_t n=readlink(linkpath,target,sizeof(target)-1);if(n<0||!strstr(target,"[ksu_driver]"))die("SukiSU fd identity");
 printf("KSU_FD_TARGET=%s\n",target);
 struct ksu_info info={0};if(ioctl(fd,0x80104b02UL,&info))die("KSU GET_INFO");
 printf("KSU_INFO version=%u flags=%u features=%u uapi=%u\n",info.version,info.flags,info.features,info.uapi_version);
 if(info.uapi_version!=2||info.features!=5||info.flags!=0||info.version!=40900)die("KSU info contract");
 char full[255]={0},hook[32]={0};if(ioctl(fd,0x80004b64UL,full)||ioctl(fd,0x80004b65UL,hook))die("KSU version hook query");
 if((full[0]!='v'||!strchr(full,'@'))||strcmp(hook,"SUSFS Inline Hook"))die("KSU source hook mismatch");
 printf("KSU_FULL_VERSION=%s\nKSU_HOOK_TYPE=%s\n",full,hook);
 struct ksu_feature f={.feature_id=2};if(ioctl(fd,0xc0004b0dUL,&f)||!f.supported||f.value!=0)die("KSU audit feature query");
 printf("KSU_AUDIT_FEATURE supported=%u value=%llu\n",f.supported,(unsigned long long)f.value);

 struct ksu_feature hide={.feature_id=4};
 if(ioctl(fd,0xc0004b0dUL,&hide)||!hide.supported||hide.value!=0)die("SELinux hide default unexpectedly enabled");
 puts("SELINUX_HIDE_DEFAULT_PASS: supported and disabled; no state change requested");
 probe_kpm(fd);
 pid_t p=fork();if(p<0)die("permission child");
 if(!p){
  if(setgroups(0,NULL)||setgid(65534)||setuid(65534)||getuid()!=65534||geteuid()!=65534)die("drop test identity");
  struct ksu_info public_info={0};if(ioctl(fd,0x80104b02UL,&public_info)||public_info.uapi_version!=2)die("unprivileged public info");
  errno=0;int r=ioctl(fd,0xc0004b0dUL,&f);if(r!=-1||errno!=EPERM)die("privileged query should be denied");
  errno=0;r=ioctl(fd,0x00004b01UL,NULL);if(r!=-1||errno!=EPERM||geteuid()!=65534)die("unauthorized root request should be denied");
  struct kpm_cmd denied_kpm={1,(uintptr_t)"/probe.kpm",0,0};
  errno=0;r=ioctl(fd,0xc0004bc8UL,&denied_kpm);if(r!=-1||errno!=EPERM)die("unprivileged KPM load denial");
  puts("KPM_PERMISSION_PASS: unauthorized loader denied before pointer access");
  puts("KSU_PERMISSION_PASS: public info readable; privileged query and unauthorized root denied");_exit(0);
 }
 int s;if(waitpid(p,&s,0)!=p||!WIFEXITED(s)||WEXITSTATUS(s))die("KSU permission child result");
 f.value=99;f.supported=0;if(ioctl(fd,0xc0004b0dUL,&f)||!f.supported||f.value!=0)die("audit setting changed");
 close(fd);puts("KSU_RUNTIME_PASS");
}

static long monotime(void) { struct timespec t;if(clock_gettime(CLOCK_MONOTONIC,&t))die("monotonic clock");return t.tv_sec; }
static void stress_worker(int cpu,int seconds) {
 cpu_set_t mask;CPU_ZERO(&mask);CPU_SET(cpu,&mask);
 if(sched_setaffinity(0,sizeof(mask),&mask)||sched_getcpu()!=cpu)die("CPU affinity");
 const size_t words=32*1024*1024/sizeof(unsigned long long);
 volatile unsigned long long *mem=mmap(NULL,words*sizeof(*mem),PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
 if(mem==MAP_FAILED)die("anonymous mmap");
 unsigned char *buf=malloc(1024*1024),*copy=malloc(1024*1024);if(!buf||!copy)die("IO buffers");
 char path[64];snprintf(path,sizeof(path),"/tmp/stress-%d",cpu);
 long begin=monotime(),deadline=begin+seconds;unsigned rounds=0;
 do {
  unsigned long long seed=0x9e3779b97f4a7c15ULL ^ ((unsigned long long)cpu<<32) ^ rounds;
  for(size_t i=0;i<words;i++)mem[i]=seed^i;
  for(size_t i=0;i<words;i++)if(mem[i]!=(seed^i))die("memory integrity");
  memset(buf,(cpu+rounds)&255,1024*1024);int fd=open(path,O_CREAT|O_TRUNC|O_RDWR,0600);if(fd<0)die("stress file open");
  if(write(fd,buf,1024*1024)!=1024*1024||fsync(fd)||pread(fd,copy,1024*1024,0)!=1024*1024||memcmp(buf,copy,1024*1024))die("stress file IO");
  struct stat st;if(fstat(fd,&st)||st.st_size!=1024*1024||close(fd)||unlink(path))die("stress stat cleanup");
  if(!(rounds%8)) {pid_t p=fork();if(p<0)die("stress fork");if(!p){execl("/init","/init","child",NULL);_exit(99);}int s;if(waitpid(p,&s,0)!=p||!WIFEXITED(s)||WEXITSTATUS(s)!=37)die("stress exec wait");}
  if(sched_getcpu()!=cpu)die("CPU migrated outside affinity");
  rounds++;
 } while(monotime()<deadline);
 printf("STRESS_CPU_PASS cpu=%d rounds=%u elapsed=%ld memory_bytes=%zu\n",cpu,rounds,monotime()-begin,words*sizeof(*mem));
 munmap((void*)mem,words*sizeof(*mem));free(buf);free(copy);_exit(0);
}
static void run_stress(void) {
 int seconds=atoi(getenv("KTEST_SECONDS")?getenv("KTEST_SECONDS"):"60");
 int cpus=sysconf(_SC_NPROCESSORS_ONLN);if(seconds<1||seconds>300||cpus<1||cpus>8)die("stress arguments");
 printf("STRESS_BEGIN cpus=%d seconds=%d\n",cpus,seconds);
 pid_t workers[8];for(int i=0;i<cpus;i++){workers[i]=fork();if(workers[i]<0)die("stress worker fork");if(!workers[i])stress_worker(i,seconds);}
 for(int i=0;i<cpus;i++){int s;if(waitpid(workers[i],&s,0)!=workers[i]||!WIFEXITED(s)||WEXITSTATUS(s))die("stress worker failed");}
 puts("STRESS_ALL_PASS");
}

int main(int argc,char **argv) {
 if(argc>1 && !strcmp(argv[1],"child")) return 37;
 int c=open("/dev/ttyAMA0",O_RDWR);if(c<0)c=open("/dev/console",O_RDWR);if(c>=0){dup2(c,0);dup2(c,1);dup2(c,2);}
 setbuf(stdout,NULL); puts("TEST_BEGIN: unchanged ARM64 Image minimal userspace");
 if(getpid()!=1)die("not PID 1");
 if(mount("proc","/proc","proc",0,NULL))die("mount proc");
 if(mount("sysfs","/sys","sysfs",0,NULL))die("mount sysfs");
 if(mount("tmpfs","/tmp","tmpfs",0,NULL))die("mount tmpfs");
 struct utsname u;if(uname(&u))die("uname");printf("UNAME_RELEASE=%s\nUNAME_VERSION=%s\nUNAME_MACHINE=%s\n",u.release,u.version,u.machine);
 if(strcmp(u.release,"6.6.118-android15-8-g93e223c276e7-abogki500782043-4k"))die("release mismatch");
 if(strcmp(u.version,"#1 SMP PREEMPT Wed Apr  8 15:08:30 UTC 2026"))die("version mismatch");
 printf("PAGE_SIZE=%ld ONLINE_CPUS=%ld\n",sysconf(_SC_PAGESIZE),sysconf(_SC_NPROCESSORS_ONLN));
 if(sysconf(_SC_PAGESIZE)!=4096)die("page size");
 for(int i=0;i<64;i++){
  int fd=open("/tmp/test",O_CREAT|O_TRUNC|O_RDWR,0600);if(fd<0)die("open");
  const char *msg="ace5pro kernel test";char b[64]={0};struct stat st;
  if(write(fd,msg,strlen(msg))!=(ssize_t)strlen(msg)||lseek(fd,0,SEEK_SET)<0||read(fd,b,sizeof(b))!=(ssize_t)strlen(msg)||strcmp(b,msg)||fstat(fd,&st)||close(fd)||unlink("/tmp/test"))die("filesystem");
  pid_t p=fork();if(p<0)die("fork");if(!p){execl("/init","/init","child",NULL);_exit(99);}int status;if(waitpid(p,&status,0)!=p||!WIFEXITED(status)||WEXITSTATUS(status)!=37)die("fork exec wait");
 }
 int p[2];char b[4]={0};if(pipe(p)||write(p[1],"ok",2)!=2||read(p[0],b,2)!=2||strcmp(b,"ok"))die("pipe");close(p[0]);close(p[1]);
 puts("TEST_CHECKS_PASSED: proc sysfs tmpfs file IO stat fork exec wait pipe");
 probe_ksu();
 run_stress();
 sleep(5);puts("TEST_PASS: kernel booted to PID 1 and completed minimal userspace checks");sync();reboot(RB_POWER_OFF);for(;;)sleep(60);
}

