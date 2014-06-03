;NSIS Modern User Interface
;Welcome/Finish Page Example Script
;Written by Joost Verburg

;--------------------------------
;Include Modern UI

  !include "MUI2.nsh"

;--------------------------------
;General


  !define M_PRODUCT "Siren"
  !define MUI_FILE "siren"
  !define M_VERSION "2.1.3"
  !define py2exeOutputDirectory 'dist'
  !define MUI_ICON "icons\siren_icon.ico"

  ;Name and file
  Name "${M_PRODUCT}"
  BrandingText "Siren"
  OutFile "install_siren.exe"

  ;Default installation folder
  InstallDir "$LOCALAPPDATA\${M_PRODUCT}_${M_VERSION}"

  ;Get installation folder from registry if available
  InstallDirRegKey HKCU "Software\${M_PRODUCT}_${M_VERSION}" ""

  ;Request application privileges for Windows Vista
  RequestExecutionLevel user

;--------------------------------
;Interface Settings

  !define MUI_ABORTWARNING

;--------------------------------
;Pages

  !insertmacro MUI_PAGE_WELCOME
  !insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
  !insertmacro MUI_PAGE_COMPONENTS
  !insertmacro MUI_PAGE_DIRECTORY
  !insertmacro MUI_PAGE_INSTFILES
  !insertmacro MUI_PAGE_FINISH

  !insertmacro MUI_UNPAGE_WELCOME
  !insertmacro MUI_UNPAGE_CONFIRM
  !insertmacro MUI_UNPAGE_INSTFILES
  !insertmacro MUI_UNPAGE_FINISH

;--------------------------------
;Languages

  !insertmacro MUI_LANGUAGE "English"

;--------------------------------
;Installer Sections

Section "Siren" SecSiren

  SetOutPath "$INSTDIR"
  File /r '${py2exeOutputDirectory}\*.*'

;create start-menu items
  CreateDirectory "$SMPROGRAMS\${M_PRODUCT}"
  CreateShortCut "$SMPROGRAMS\${M_PRODUCT}\Uninstall.lnk" "$INSTDIR\Uninstall.exe" "" "$INSTDIR\icons\usiren_icon.ico" 0
  CreateShortCut "$SMPROGRAMS\${M_PRODUCT}\${M_PRODUCT}.lnk" "$INSTDIR\${MUI_FILE}.exe" "" "$INSTDIR\icons\siren_icon.ico" 0
 
;write uninstall information to the registry
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${M_PRODUCT}" "DisplayName" "${M_PRODUCT} (remove only)"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${M_PRODUCT}" "UninstallString" "$INSTDIR\Uninstall.exe"

  ;Create uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"

SectionEnd

;--------------------------------
;Descriptions

  ;Language strings
  LangString DESC_SecSiren ${LANG_ENGLISH} "Siren Interactive mining and visualization of geospatial redescriptions."

  ;Assign language strings to sections
  !insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${SecSiren} $(DESC_SecSiren)
  !insertmacro MUI_FUNCTION_DESCRIPTION_END

;--------------------------------
;Uninstaller Section

Section "Uninstall"

;Remove the installation directory
  RMDir "$INSTDIR"
 
;Delete Start Menu Shortcuts
  Delete "$SMPROGRAMS\${M_PRODUCT}\*.*"
  RmDir  "$SMPROGRAMS\${M_PRODUCT}"
 
;Delete Uninstaller And Unistall Registry Entries
  DeleteRegKey HKEY_LOCAL_MACHINE "SOFTWARE\${M_PRODUCT}"
  DeleteRegKey HKEY_LOCAL_MACHINE "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\${M_PRODUCT}"  
  Delete "$INSTDIR\Uninstall.exe"

SectionEnd

