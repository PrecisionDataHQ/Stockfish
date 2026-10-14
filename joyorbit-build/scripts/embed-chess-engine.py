"""Package the source-built Stockfish executable as an extracted native asset."""
from pathlib import Path
import os
import hashlib
import json
import shutil
import subprocess
import zipfile
ROOT=Path(__file__).resolve().parents[1]
binary=ROOT/'build/stockfish/android/libjoyorbit_stockfish.so'
if not binary.is_file(): raise SystemExit('Build pinned Stockfish with prepare-stockfish.py first.')
module=ROOT/'build/chess-engine'
module.mkdir(parents=True,exist_ok=True)
target=module/'jniLibs/arm64-v8a'
target.mkdir(parents=True,exist_ok=True)
shutil.copy2(binary,target/binary.name)
assets=module/'assets/joyorbit/chess'
assets.mkdir(parents=True,exist_ok=True)
(assets/'engine.json').write_text(json.dumps({'engine':'Stockfish19','source':'edb0d9db6731067ec50ce619ff372b463bc4dd5d','binary_sha256':hashlib.file_digest(binary.open('rb'),'sha256').hexdigest()}))
template=ROOT/'build/android-apk'
shutil.copytree(template/'gradle',module/'gradle',dirs_exist_ok=True)
shutil.copy2(template/'gradlew',module/'gradlew')
(module/'settings.gradle').write_text("pluginManagement { repositories { google(); mavenCentral(); gradlePluginPortal() } }\ndependencyResolutionManagement { repositories { google(); mavenCentral() } }\nrootProject.name='chess-engine'\n")
(module/'local.properties').write_text('sdk.dir='+os.environ['ANDROID_SDK_ROOT']+'\n')
(module/'AndroidManifest.xml').write_text('<manifest xmlns:android="http://schemas.android.com/apk/res/android"/>\n')
(module/'build.gradle').write_text("""plugins { id 'com.android.library' version '9.1.0' }
android {
 namespace 'io.precisiondata.joyorbit.chess.engine'
 compileSdk 36
 ndkVersion '29.0.14206865'
 defaultConfig { minSdk 24 }
 sourceSets { main { manifest.srcFile 'AndroidManifest.xml'; jniLibs.srcDirs=['jniLibs']; assets.srcDirs=['assets'] } }
}
""")
subprocess.run(['sh',str(module/'gradlew'),'-p',str(module),'assembleDebug','--no-daemon'],check=True)
output=ROOT/'build/android-apk/libs/joyorbit-chess-engine.aar'
with zipfile.ZipFile(module/'build/outputs/aar/chess-engine-debug.aar') as source, zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as archive:
    # Android's packaging strips symbols; stamp the actual packaged executable.
    compiled=source.read('jni/arm64-v8a/libjoyorbit_stockfish.so')
    stamp=json.loads(source.read('assets/joyorbit/chess/engine.json'))
    stamp['binary_sha256']=hashlib.sha256(compiled).hexdigest()
    for entry in source.infolist():
        archive.writestr(entry,json.dumps(stamp).encode() if entry.filename=='assets/joyorbit/chess/engine.json' else source.read(entry.filename))
print('Stockfish executable embedded; app-process execution still requires runtime verification.')
