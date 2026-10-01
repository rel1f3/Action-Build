// Exact pure version gate copied from manager source 904c60d18f026340ce38ca2d5a1da529aadcba1a.
// Inputs come from the actual QEMU ioctl output, not Android authentication mocks.
object NativesGate {
 const val MINIMAL_SUPPORTED_KERNEL=32513
 const val MINIMAL_SUPPORTED_KERNEL_FULL="v4.0.0"
 var version=40900
 var full="v4.2.0-b20dee70@HEAD"
 var kernelUAPIVersion=2
 var managerUAPIVersion=2
 fun getFullVersion():String=full
    fun isVersionLessThan(v1Full: String, v2Full: String): Boolean {
        fun extractVersionParts(version: String): List<Int> {
            val match = Regex("""v\d+(\.\d+)*""").find(version)
            val simpleVersion = match?.value ?: version
            return simpleVersion.trimStart('v').split('.').map { it.toIntOrNull() ?: 0 }
        }

        val v1Parts = extractVersionParts(v1Full)
        val v2Parts = extractVersionParts(v2Full)
        val maxLength = maxOf(v1Parts.size, v2Parts.size)
        for (i in 0 until maxLength) {
            val num1 = v1Parts.getOrElse(i) { 0 }
            val num2 = v2Parts.getOrElse(i) { 0 }
            if (num1 != num2) return num1 < num2
        }
        return false
    }
    fun checkUAPIMismatch(): Boolean {
        return kernelUAPIVersion != managerUAPIVersion
    }
    fun requireNewKernel(): Boolean {
        if (version != -1 && version < MINIMAL_SUPPORTED_KERNEL) return true
        return (isVersionLessThan(getFullVersion(), MINIMAL_SUPPORTED_KERNEL_FULL)) || checkUAPIMismatch()
    }
}
fun main(args:Array<String>) {
 NativesGate.full="builtin-b20dee702035af09cb2ecb5f35443bbc1747f3e6@custom-pair40900"
 check(NativesGate.requireNewKernel())
 for(branch in listOf("HEAD","builtin")) {
  NativesGate.full="v4.2.0-b20dee70@"+branch
  check(!NativesGate.requireNewKernel())
 }
 NativesGate.full="v4.2.0-SukiSU-Ultra-unknown@unknown"
 check(!NativesGate.requireNewKernel())
 NativesGate.kernelUAPIVersion=4
 check(NativesGate.requireNewKernel())
 NativesGate.kernelUAPIVersion=2
 NativesGate.full="v3.9.9-b20dee70@HEAD"
 check(NativesGate.requireNewKernel())
 NativesGate.full=args[0];NativesGate.version=args[1].toInt();NativesGate.kernelUAPIVersion=args[2].toInt()
 check(!NativesGate.requireNewKernel())
 println("EXACT_MANAGER_GATE_PASS full="+NativesGate.full+" requiresNewKernel=false")
}

