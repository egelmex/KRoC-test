#!/usr/bin/env python
import sys
import os
import datetime
import subprocess
import glob

# Pick the remaining packages from the common directory
sys.path.append('../common/python-lib')
from distribution_tools.copy import mkdirs, copy_file, copy_files, copy_tree
from distribution_tools.download import download
from distribution_tools.archive import extract
from distribution_tools import command

BUILD               = 'build'
OUTPUT              = 'output'
APP_DIR             = os.path.join(OUTPUT, 'Transterpreter.app')
CONTENTS_DIR        = os.path.join(APP_DIR, 'Contents')
RESOURCE_DIR        = os.path.join(CONTENTS_DIR, 'Resources')
BIN_DIR             = os.path.join(RESOURCE_DIR, 'bin')
FRAMEWORK_DIR       = os.path.join(CONTENTS_DIR, 'Frameworks')
JEDIT_DIR           = os.path.join(RESOURCE_DIR, 'jEdit')
SYSTEM_FRAMEWORK_DIR= '/System/Library/Frameworks'

POSIX_TVM_INC_DIR   = os.path.join(RESOURCE_DIR, 'posix', 'tvm', 'include')
POSIX_TVM_LIB_DIR   = os.path.join(RESOURCE_DIR, 'posix', 'tvm', 'lib')
POSIX_TVM_FW_DIR    = os.path.join(RESOURCE_DIR, 'posix', 'tvm', 'firmware')

POSIX_TVMPPC_INC_DIR= os.path.join(RESOURCE_DIR, 'posix', 'tvm-ppc', 'include')
POSIX_TVMPPC_LIB_DIR= os.path.join(RESOURCE_DIR, 'posix', 'tvm-ppc', 'lib')
POSIX_TVMPPC_FW_DIR = os.path.join(RESOURCE_DIR, 'posix', 'tvm-ppc', 'firmware')

ARDUINO_TVM_INC_DIR = os.path.join(RESOURCE_DIR, 'arduino', 'tvm', 'include')
ARDUINO_TVM_LIB_DIR = os.path.join(RESOURCE_DIR, 'arduino', 'tvm', 'lib')
ARDUINO_TVM_FW_DIR  = os.path.join(RESOURCE_DIR, 'arduino', 'tvm', 'firmware')
ARDUINO_PLUMBING_DIR= os.path.join(OUTPUT, 'arduino', 'plumbing-book')
ARDUINO_TVM_CONF_DIR= os.path.join(RESOURCE_DIR, 'arduino', 'tvm', 'conf')

JEDIT_OSX_PLUGIN    = 'MacOSX.jar'

SPARKLE             = 'Sparkle 1.5b6'
SPARKLE_ZIP         = SPARKLE + '.zip'
SPARKLE_FEED        = '=http://download.transterpreter.org/appcast/mac-dev.xml'

LIPO_BINARIES       = ['occ21', 'tvm', 'ilibr', 'mkoccdeps'] 
# FIXME: tranx86 did not seem to get built?
BINARIES            = 'kmakef kroc occbuild plinker.pl tce-dump.pl'.split()
LIBRARIES           = ('libSDL*.dylib libplayer*.dylib liboccam_*.a ' + 
                        'tvm/liboccam_tvm_*.dylib libkrocif.a libccsp.a').split()

build_date  = datetime.datetime.utcnow()
version     = build_date.strftime('%Y%m%d.%H%M')
svnversion  = command.capture(['svnversion', '-nc', '../../'])
shortversion= 'Development version: %s (%s)' % (version, svnversion)

# Make the top level directories, in case they don't exist
mkdirs(OUTPUT)
mkdirs(BUILD)
mkdirs(BIN_DIR)
mkdirs(ARDUINO_TVM_CONF_DIR)

# Download and extract sparkle
download(os.path.join(BUILD, SPARKLE_ZIP),
        'http://sparkle.andymatuschak.org/files/%s' % (SPARKLE_ZIP, ))
extract(os.path.join(BUILD, SPARKLE_ZIP), BUILD)

# FIXME: Perhaps we should include this in the repos as it is more obscure than
# the other things we depend on and therefore more likely to go away
# from: http://www.seph.dk/uncategorized/new-mac-os-x-plugin-for-jedit/
# FIXME: Is this even required with the new version of jedit?
download(os.path.join(BUILD, JEDIT_OSX_PLUGIN),
        'http://www.seph.dk/download/$JEDIT_OSX_PLUGIN')

# Copy the .app skeleton
# FIXME: There are some .in files in here that need transforming!!!
copy_tree('skel/Transterpreter.app', 
          APP_DIR, 
          substitute=dict(version=version,
                          shortversion=shortversion,
                          sparkle_feed=SPARKLE_FEED))
# Copy the Java application stub
copy_file(
        os.path.join(SYSTEM_FRAMEWORK_DIR, 
            'JavaVM.framework/Resources/MacOS/JavaApplicationStub'),
        os.path.join(APP_DIR, 'Contents/MacOS/'))

# Binaries
for bin in BINARIES:
    copy_file(os.path.join('install/bin/', bin), BIN_DIR)
for bin in LIPO_BINARIES:
    command.execute(
            ['lipo', '-create', os.path.join('install/bin', bin) , 
                os.path.join('install-tvm-ppc/bin/', bin), '-output', 
                os.path.join(BIN_DIR, bin)])

# Sparkle
copy_tree(
        os.path.join(BUILD, SPARKLE, 'Sparkle.framework'),
        os.path.join(FRAMEWORK_DIR, 'Sparkle.framework'))

# tvm native libraries
# FIXME: These should go elsewhere
for lib in LIBRARIES:
    copy_files(os.path.join('install/lib/', lib), BIN_DIR)


# tvm posix includes, libs and firmware
mkdirs(POSIX_TVM_INC_DIR)
mkdirs(POSIX_TVM_LIB_DIR)
mkdirs(POSIX_TVM_FW_DIR)
copy_tree('install/share/tvm/vtinclude', POSIX_TVM_INC_DIR)
copy_tree('install/share/tvm/vtlib', POSIX_TVM_LIB_DIR)
copy_file('install/share/tvm/firmware/tvm-posix.tbc', POSIX_TVM_FW_DIR)

# tvm-ppc posix includes, libs and firmware
copy_tree('install-tvm-ppc/share/tvm/vtinclude', POSIX_TVMPPC_INC_DIR)
copy_tree('install-tvm-ppc/share/tvm/vtlib', POSIX_TVMPPC_LIB_DIR)
copy_file('install-tvm-ppc/share/tvm/firmware/tvm-posix.tbc', POSIX_TVMPPC_FW_DIR)

# kroc posix includes, libs and firmware
# FIXME: I don't currently see these haning around... so lets leave them out
#copydir "install/share/kroc" "$outputDir/$rezDir/share/kroc"

# Arduino firmware
copy_files('build/kroc-tvm-avr-*-*-wrapper/tvm-avr-*-*.hex', ARDUINO_TVM_FW_DIR)

# Arduino config files
for conf in glob.iglob('../../tvm/arduino/occam/conf/*.conf.in'):
    copy_file(conf, 
              os.path.join(ARDUINO_TVM_CONF_DIR, os.path.basename(conf)[:-3]))

# Arduino tools
# FIXME: These will have to be py2exed I think...
copy_file('../../tvm/arduino/scripts/binary-to-ihex', BIN_DIR)
copy_file('../../tvm/arduino/scripts/read-arduino', BIN_DIR)
copy_file('install-avr/bin/avr-occbuild', BIN_DIR)

# Arduino includes
copy_tree('../../tvm/arduino/occam/include', ARDUINO_TVM_INC_DIR, excludes='.ss')

# Plumbing examples
mkdirs(ARDUINO_PLUMBING_DIR)
copy_files('../../tvm/arduino/occam/book/ch*.occ', ARDUINO_PLUMBING_DIR)

# arduino module includes
copy_tree('install-avr/share/tvm/avr-vtinclude', ARDUINO_TVM_LIB_DIR)

# arduino module libs
copy_tree('install-avr/share/tvm/avr-vtlib', ARDUINO_TVM_LIB_DIR)

# Avrdude
copy_file('install/bin/avrdude', BIN_DIR)
copy_file('install/etc/avrdude.conf', BIN_DIR)

# JEdit
mkdirs(JEDIT_DIR)
copy_tree('build/jedit/jedit-program', JEDIT_DIR, excludes=['LatestVersion.jar'])
copy_file('build/occPlug/OccPlug.jar', os.path.join(JEDIT_DIR, 'jars'))
copy_file('../common/jEdit/occam-pi.xml', os.path.join(JEDIT_DIR, 'modes'))

# OS X Plugin
# FIXME: Still required with jEdit 4.3.2????
copy_file(os.path.join(BUILD, JEDIT_OSX_PLUGIN), os.path.join(JEDIT_DIR, 'modes'))

# Updater
copy_file('build/macupdater/JEditSparklePlugin.jar', os.path.join(JEDIT_DIR, 'jars'))

# Copy custom properties
copy_file('../common/jEdit/properties.props', os.path.join(JEDIT_DIR, 'properties'))

# Add the occam-pi modeline
s = open('build/jedit/jedit-program/modes/catalog', 'r')
d = open(os.path.join(JEDIT_DIR, 'modes/catalog'), 'w')
for l in s:
    if l.startswith('</MODES>'):
      d.write('<MODE NAME="occam-pi" FILE="occam-pi.xml" FILE_NAME_GLOB="*.{occ,module}" />\n')
    d.write(l)
s.close()
d.close()

copy_file('skel/README.rtf', OUTPUT)


print 'Built app version: %s (%s)' % (version, shortversion,)