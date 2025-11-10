; MEMEFinder 安装脚本 - Inno Setup
; 使用 Inno Setup Compiler 编译此脚本

#define MyAppName "MEMEFinder"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "aliveriver"
#define MyAppURL "https://github.com/aliveriver/MEMEFinder"
#define MyAppExeName "MEMEFinder.exe"

[Setup]
; 应用基本信息
AppId={{A1B2C3D4-E5F6-4A5B-8C9D-0E1F2A3B4C5D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
; LicenseFile=LICENSE
; 输出设置
OutputDir=installer
OutputBaseFilename=MEMEFinder-Setup-v{#MyAppVersion}
; SetupIconFile=icon.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
; 权限和兼容性
PrivilegesRequired=lowest
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
; 界面设置
DisableProgramGroupPage=yes
DisableWelcomePage=no
DisableDirPage=no
; 确保用户可以选择安装路径

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
; 如果您的 Inno Setup 安装了中文语言包，取消下面这行的注释
; Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "downloadmodels"; Description: "安装后自动下载 AI 模型（推荐，需要网络）"; GroupDescription: "初始化设置:"; Flags: checkedonce

[Files]
; 主程序文件
Source: "..\dist\MEMEFinder\MEMEFinder.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\MEMEFinder\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs
; 文档（从项目根目录复制）
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion; DestName: "README.txt"
; 空目录（在安装后创建）
; logs 和 models 目录会在运行时自动创建

[Dirs]
Name: "{app}\logs"
Name: "{app}\models"

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{group}\下载 AI 模型"; Filename: "{app}\{#MyAppExeName}"; Parameters: "download_models.py"
Name: "{group}\用户指南"; Filename: "{app}\docs\USER_GUIDE.md"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; 安装完成后运行
Filename: "{app}\{#MyAppExeName}"; Parameters: "download_models.py"; Description: "下载 AI 模型（首次必须）"; Flags: postinstall skipifsilent nowait; Tasks: downloadmodels
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: postinstall skipifsilent nowait; Check: not WizardIsTaskSelected('downloadmodels')

[Code]
var
  DownloadPage: TOutputProgressWizardPage;
  
procedure InitializeWizard;
begin
  DownloadPage := CreateOutputProgressPage('下载 AI 模型', '正在下载必需的 AI 模型文件...');
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  
  if (CurPageID = wpReady) and WizardIsTaskSelected('downloadmodels') then
  begin
    DownloadPage.SetText('准备下载模型...', '');
    DownloadPage.SetProgress(0, 0);
    DownloadPage.Show;
    
    try
      DownloadPage.SetText('正在下载 PaddleOCR 模型...', '这可能需要 5-15 分钟');
      
      // 注意：实际下载在安装后的 [Run] 节中执行
      // 这里只是显示进度页面
      
      DownloadPage.SetProgress(100, 100);
    finally
      DownloadPage.Hide;
    end;
  end;
end;

[UninstallDelete]
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\models"
Type: filesandordirs; Name: "{app}\meme_finder.db"
Type: filesandordirs; Name: "{app}\__pycache__"
