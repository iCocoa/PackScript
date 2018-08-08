#!/usr/bin/env python
# _*_ coding:utf-8 _*_

import subprocess
import os
import json
import re

SVN_USERNAME = 'Hansen'
SVN_PASSWORD = '123456'
SVN_URL = 'https://Hansen@svn.domain.com/svn/****/trunk/iOS/packProject'
CHECKOUT_FOLDER = 'ios_source_code'
MacOS_ADMIN_USER = 'packrobot'
MacOS_ADMIN_PASSWORD = '123456'
EXPORT_MAIN_DIRECTORY = "/Users/%s/Documents/ios_appArchive/" % MacOS_ADMIN_USER
PROVISONING_PROFILE_DIRECTORY = "/Users/%s/Library/MobileDevice/Provisioning Profiles/" % MacOS_ADMIN_USER


def json_load_byteified(file_handle):
    return _byteify(
        json.load(file_handle, object_hook=_byteify),
        ignore_dicts=True
    )

def json_loads_byteified(json_text):
    return _byteify(
        json.loads(json_text, object_hook=_byteify),
        ignore_dicts=True
    )

def _byteify(data, ignore_dicts = False):
    # if this is a unicode string, return its string representation
    if isinstance(data, unicode):
        return data.encode('utf-8')
    # if this is a list of values, return list of byteified values
    if isinstance(data, list):
        return [ _byteify(item, ignore_dicts=True) for item in data ]
    # if this is a dictionary, return dictionary of byteified keys and values
    # but only if we haven't already byteified it
    if isinstance(data, dict) and not ignore_dicts:
        return {
            _byteify(key, ignore_dicts=True): _byteify(value, ignore_dicts=True)
            for key, value in data.iteritems()
        }
    # if it's anything else, return it in its original form
    return data

def currentDir():
    return os.path.split(os.path.realpath(__file__))[0]

def checkoutPath():
    return currentDir() + '/' + CHECKOUT_FOLDER

def pullSvnSourceCode():
    svnChekoutCmd = 'svn co --username=%s --password=%s %s %s' %(SVN_USERNAME, SVN_PASSWORD, SVN_URL, checkoutPath())
    p = subprocess.Popen(svnChekoutCmd, shell=True, stderr=subprocess.PIPE)
    p.wait()
    if p.returncode != 0:
        print ('[packageFailed]: %s') %p.stderr.read()
    else:
        print ('Sucessfullly checkout source code at path: %s') %(checkoutPath())

def clearDir(Dir):
    cleanCmd = "rm -r %s" %(Dir)
    process = subprocess.Popen(cleanCmd, shell=True)
    (stdoutdata, stderrdata) = process.communicate()

def getAppConfig():
    projectWWWDir = 'packProject/www'
    destinationWWWDir = currentDir() + '/' + CHECKOUT_FOLDER + '/' + projectWWWDir;
    appConfigFilePath = destinationWWWDir + '/appConfig.json'
    if os.path.exists(appConfigFilePath):
        appConfigReader = open(appConfigFilePath, 'r')
        appConfig = json_load_byteified(appConfigReader)
        appConfigReader.close()
        return appConfig
    return None


def copyFiles(sourceDir, destinationDir):
    if not os.path.exists(sourceDir):
        print ('[packageFailed]: Copy file -- sourceDir doesn\'t exist ')
        pass

    clearDir(destinationDir)
    for file in os.listdir(sourceDir):
        sourceFile = os.path.join(sourceDir, file)
        destinationFile = os.path.join(destinationDir, file)
        if os.path.isfile(sourceFile):
            if not os.path.exists(destinationDir):
                os.makedirs(destinationDir)
            if not os.path.exists(destinationFile) or (os.path.exists(destinationFile) and (os.path.getsize(destinationFile) != os.path.getsize(sourceFile))):
                open(destinationFile, "wb").write(open(sourceFile, "rb").read())
        if os.path.isdir(sourceFile):
            copyFiles(sourceFile, destinationFile)
    print ('Copy assets success!')

def copyFile(srcFile, dstFile):
    srcReader = open(srcFile, "rb")
    desWriter = open(dstFile, "wb")
    desWriter.write(srcReader.read())
    srcReader.close()
    desWriter.close()

def cleanArchiveFile(archiveFile):
    cleanCmd = "rm -r %s" %(archiveFile)
    process = subprocess.Popen(cleanCmd, shell=True)
    (stdoutdata, stderrdata) = process.communicate()

def buildExportDirectory():
    dateCmd = 'date "+%Y-%m-%d_%H-%M-%S"'
    process = subprocess.Popen(dateCmd, stdout=subprocess.PIPE, shell=True)
    (stdoutdata, stderrdata) = process.communicate()
    exportDirectory = "%s%s" %(EXPORT_MAIN_DIRECTORY, stdoutdata.strip())
    return exportDirectory

def getMobileProvisionItem(filepath, key):
    cmd = 'mobileprovision-read -f %s -o %s' %(filepath ,key)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    p.wait()
    return removeControlChars(p.stdout.read())

def updatePlistEntry(filePath, key, value):
    cmd = "/usr/libexec/PlistBuddy -c 'Set :%s %s' %s" % (key, value, filePath)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.wait()
    if p.returncode != 0:
        print p.stderr.read()

def deletePlistEntry(filePath, key):
    cmd = "/usr/libexec/PlistBuddy -c 'Delete :%s' %s" %(key, filePath)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.wait()
    if p.returncode != 0:
        print p.stderr.read()

def addPlistEntry(filePath, key, _type, value):
    cmd = "/usr/libexec/PlistBuddy -c 'Add :%s %s %s' %s" % (key, _type, value, filePath)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.wait()
    if p.returncode != 0:
        print p.stderr.read()

def findFileInDirectory(ext, dir):
    fileName = ''
    items = os.listdir(dir)
    for name in items:
        if name.endswith(ext):
            fileName = name
            break
    if not len(fileName) > 0:
        return ''
    return dir + '/' + fileName

def removeControlChars(s):
    control_chars = ''.join(map(unichr, range(0,32) + range(127,160)))
    control_char_re = re.compile('[%s]' % re.escape(control_chars))
    return control_char_re.sub('', s)


def main():

    # Pull ios project source code from svn.
    pullSvnSourceCode()

    # Copy 'www' files.
    sourceWWWDir = currentDir() + '/www'
    projectWWWDir = '/packProject/www'
    destinationWWWDir = checkoutPath() + projectWWWDir
    copyFiles(sourceWWWDir, destinationWWWDir)
    for file in os.listdir(destinationWWWDir):
        if file.startswith('secret.json') or file.endswith('.mobileprovision') or file.endswith('.p12'):
            os.remove(destinationWWWDir + '/' + file)

    # Copy app icons.
    iconAssetDirectory = checkoutPath() + '/packProject/Assets.xcassets/AppIcon.appiconset'
    iconSrcDirectory = projectWWWDir + '/Icons/ios'
    items = os.listdir(iconSrcDirectory)
    for filename in items:
        copyFile(iconSrcDirectory + '/' + filename, iconAssetDirectory + '/' + filename)
    clearDir(iconSrcDirectory)

    # Copy launch images.
    launchImageAssetDirectory = checkoutPath() + '/packProject/Assets.xcassets/LaunchImage.launchimage'
    LaunchImageSrcDirectory = projectWWWDir + '/LaunchImages/ios'
    items = os.listdir(LaunchImageSrcDirectory)
    for filename in items:
        copyFile(LaunchImageSrcDirectory + '/' + filename, launchImageAssetDirectory + '/' + filename)
    clearDir(LaunchImageSrcDirectory)

    # Read 'appConfig.json' file.
    appConfig = getAppConfig()
    if appConfig is None:
        print ("[packageFailed]: Not found \'%s\' file in \'www\' directory.") % ('appConfig.json')
        return
    versionName = appConfig['version']['name']
    versionCode = int(appConfig['version']['code'])
    applicationId = appConfig['id']
    appName = appConfig['appName']
    mode = 'Debug' if appConfig['debug'] else 'Release'

    # Modify 'info.plist' file in project/workspace according to appconfig params those read from 'appConfig.json' file.
    infoPlistPath = checkoutPath() + '/packProject/' + 'info.plist'
    updatePlistEntry(infoPlistPath, 'CFBundleShortVersionString', versionName)
    updatePlistEntry(infoPlistPath, 'CFBundleVersion', versionCode)
    updatePlistEntry(infoPlistPath, 'CFBundleIdentifier', applicationId)
    updatePlistEntry(infoPlistPath, 'CFBundleDisplayName', appName)

    # Get p12 file's password.
    secretFilePath = sourceWWWDir + '/secret.json'
    if os.path.exists(secretFilePath):
        secretReader = open(secretFilePath, 'r')
        secretKeyDict = json_load_byteified(secretReader)
        secretReader.close()
    else:
        print ("[packageFailed]: Not found \'%s\' file in \'www\' directory.") % ('secret.json')
        return
    iosKeyDict = secretKeyDict['ios'] if 'ios' in secretKeyDict else None
    p12Password = iosKeyDict['p12Password'] if 'p12Password' in iosKeyDict else '123456'

    # Import p12 file into system keychain.
    p12FilePath = findFileInDirectory('.p12', sourceWWWDir)
    unlockKeychainCmd = 'security unlock-keychain -p %s' %MacOS_ADMIN_PASSWORD
    p = subprocess.Popen(unlockKeychainCmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.wait()
    if p.returncode != 0:
        print p.stderr.read()
        return
    importCertCmd = 'security import %s -P %s -T /usr/bin/codesign' % (p12FilePath, p12Password)
    p = subprocess.Popen(importCertCmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.wait()
    if p.returncode != 0:
        print p.stderr.read()

    # Read mobileprovision profile info.
    provisionFileExtension = '.mobileprovision'
    provisionFilePath = findFileInDirectory(provisionFileExtension, sourceWWWDir)
    if not len(provisionFilePath) > 0:
        print ("[packageFailed]: Not found \'%s\' file in \'www\' directory.") %(provisionFileExtension)
        return
    teamIdentifier = getMobileProvisionItem(provisionFilePath, 'TeamIdentifier')
    provisionUUID = getMobileProvisionItem(provisionFilePath, 'UUID')
    provisionName = getMobileProvisionItem(provisionFilePath, 'Name')
    # type – prints mobileprovision profile type (debug, ad-hoc, enterprise, appstore)
    provisionType = getMobileProvisionItem(provisionFilePath, 'type')
    teamName = getMobileProvisionItem(provisionFilePath, 'TeamName')
    desProvisionFilePath = PROVISONING_PROFILE_DIRECTORY + provisionUUID + provisionFileExtension
    copyFile(provisionFilePath, desProvisionFilePath)

    # Build
    archiveName = "%s_%s.xcarchive" % (applicationId, versionName)
    archiveFilePath = currentDir() + '/' + archiveName
    xcworkspaceFilePath = findFileInDirectory('.xcworkspace', checkoutPath())
    projectSettingParams = 'PRODUCT_BUNDLE_IDENTIFIER=%s PROVISIONING_PROFILE_SPECIFIER=%s PROVISIONING_PROFILE=%s' %(applicationId, provisionName, provisionUUID)
    archiveCmd = 'xcodebuild -workspace %s -scheme %s -configuration %s archive -archivePath %s -destination generic/platform=iOS build %s' % (xcworkspaceFilePath, 'packProject', mode, archiveFilePath, projectSettingParams)
    p = subprocess.Popen(archiveCmd, shell=True, stderr=subprocess.PIPE)
    p.wait()
    if p.returncode != 0:
        print ("[packageFailed]: %s") %p.stderr.read()
        return

    # Create 'exportOptions.plist' file
    exportOptionsPlistFilePath = currentDir() + '/' + 'exportOptions.plist'
    addPlistEntry(exportOptionsPlistFilePath, 'provisioningProfiles', 'dict', '')
    addPlistEntry(exportOptionsPlistFilePath, 'provisioningProfiles:'+ applicationId, 'string', provisionUUID)
    addPlistEntry(exportOptionsPlistFilePath, 'teamID', 'string', teamIdentifier)
    # {app-store, ad-hoc, enterprise, development}
    method = 'development' if cmp(provisionType, 'debug') == 0 else provisionType
    method = 'app-store' if cmp(method, 'appstore') == 0 else method
    addPlistEntry(exportOptionsPlistFilePath, 'method', 'string', method)
    exportDirectory = buildExportDirectory()
    exportCmd = "xcodebuild -exportArchive -archivePath %s -exportPath %s -exportOptionsPlist %s" % (archiveFilePath, exportDirectory, exportOptionsPlistFilePath)
    p = subprocess.Popen(exportCmd, shell=True, stderr=subprocess.PIPE)
    p.wait()
    if p.returncode != 0:
        print ("[packageFailed]: %s") %p.stderr.read()
    else:
        ipaVersion = str(versionCode) if mode == 'Debug' else versionName
        ipaName = applicationId + '_' + ipaVersion + '.ipa'
        os.rename(exportDirectory + '/packProject.ipa', exportDirectory + '/' + ipaName)
        print("[packageName]: %s") % (ipaName)
        print("[packagePath]: %s") % (exportDirectory)

    cleanArchiveFile(archiveFilePath)

    p = subprocess.Popen('security lock-keychain', shell=True)
    p.wait()

if __name__ == '__main__':
    main()

