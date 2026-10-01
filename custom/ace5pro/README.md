# Ace5 Pro independent profile

Upstream-owned files remain unchanged at `1769d3eb8e81`. Regenerate the independent
workflow with `python3 custom/ace5pro/generate.py`, review it, then run `--check`.
Generation and the build readiness check fail without the independently verified
signed manager artifact pin. Its original manifest bytes/digest, APK digest,
source/UAPI/version, package/certificate, run/artifact and workflow commit are bound
in `profile.json`. This verifies the supplied signing evidence; kernel compilation
does not independently repeat Android APK installation or root authorization.
The generated workflow copies upstream build mechanics; `generate.py` contains
the small integration changes. No private SUSFS port or extra test workflow is shipped.

The manager source is official `904c60d18f02`, version 40900/UAPI2. The maintained
kernel builtin is `b20dee702035`, UAPI2, with SUSFS 2.3.0 `eba2a88a5ba3`.
Matching UAPI numbers alone do not prove every optional manager function works.
Builtin does not implement the newer CPU/uname ioctl 104/105; no fake result is added.

40900 is a **custom pairing build ID**, not an official kernel release number.
The real builtin SHA is retained in `KSU_VERSION_FULL`. The certificate table is
restricted to the requested public certificate; the native APK/package parser
and actual UAPI are unchanged. No private signing key is stored here.

The sole source compatibility adjustment matches the static-key declarations and
reads in three common-kernel consumers to the builtin's existing bool gate.
The older SUSFS patch contains no newer post-exec protocol to remove or emulate.
Original vendor target discovery is retained and filtered to the two known 4K targets.

Source version must actually be 6.6.118 before applying the requested display label.
Source SHAs, true driver identity and final Image hashes are recorded separately.
HMBIRD and Unicode fixes are enabled; optional ZRAM/LZ4/network enhancements are off.
Inherited upstream ABI relaxations do not prove vendor-module compatibility.

KPM requires the pinned `patch_linux` checksum and a changed nonempty processed
Image. Final banner, 4K header, embedded config and compiled manager identity are
checked. A changed Image/config alone is not evidence of successful KPM loading;
runtime verification is performed separately on the packaged final Image.
Android root authorization, device boot, vendor modules and display remain untested
until independently checked. The workflow never modifies stock boot or flashes a phone.
