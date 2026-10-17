"""Patch the CI-generated Capacitor android/app/build.gradle: stable signing + versionCode/versionName."""
import re, sys
name, code = sys.argv[1], sys.argv[2]
p = 'android/app/build.gradle'
s = open(p).read()
s = re.sub(r'versionCode\s+\d+', 'versionCode ' + code, s)
s = re.sub(r'versionName\s+"[^"]*"', 'versionName "' + name + '"', s)
cfg = '''    signingConfigs {
        varnethryl {
            storeFile file("varnethryl-release.jks")
            storePassword System.getenv("VARNETHRYL_KEYSTORE_PASSWORD")
            keyAlias System.getenv("VARNETHRYL_KEY_ALIAS")
            keyPassword System.getenv("VARNETHRYL_KEY_PASSWORD")
        }
    }
'''
s = s.replace('    buildTypes {', cfg + '    buildTypes {', 1)
s = re.sub(r'(buildTypes\s*\{\s*)', r'\1debug {\n            signingConfig signingConfigs.varnethryl\n        }\n        ', s, count=1)
s = re.sub(r'(release\s*\{)', r'\1\n            signingConfig signingConfigs.varnethryl', s, count=1)
open(p, 'w').write(s)
assert 'signingConfigs.varnethryl' in s and 'versionCode ' + code in s
