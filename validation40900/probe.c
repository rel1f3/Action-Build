/* Disposable KPM: no hooks, writes, kernel symbols, or device interaction.
 * ABI: KernelPatch kpmodule.h at 87f4dab2da53eca64af5175c8bdd36ca046fb875.
 * The control result proves execution of loaded code rather than config flags.
 */
#define INFO(k,v) static const char info_##k[] __attribute__((used,section(".kpm.info"),aligned(1))) = #k "=" v
INFO(name,"ace5pro-ci-probe");
INFO(version,"1.0.0");
INFO(license,"GPL v2");
INFO(author,"Action-Build CI");
INFO(description,"Inert CI module; no hooks or symbols");
static long probe_init(const char *args, const char *event, void *reserved) { return 0; }
static long probe_control(const char *args, char *output, int size) { return 73; }
static long probe_exit(void *reserved) { return 0; }
static long (*initcall)(const char *,const char *,void *) __attribute__((used,section(".kpm.init")))=probe_init;
static long (*ctlcall)(const char *,char *,int) __attribute__((used,section(".kpm.ctl0")))=probe_control;
static long (*exitcall)(void *) __attribute__((used,section(".kpm.exit")))=probe_exit;
