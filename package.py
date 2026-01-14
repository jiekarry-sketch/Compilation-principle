#!/usr/bin/env python
# package.py - 一键打包脚本
import os
import shutil
import subprocess
import sys
from datetime import datetime


def clean_build():
    """清理之前的构建文件"""
    dirs_to_remove = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"已删除: {dir_name}")

    # 清理src中的缓存文件
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            cache_dir = os.path.join(root, '__pycache__')
            shutil.rmtree(cache_dir)
            print(f"已删除: {cache_dir}")

    # 清理.pyc文件
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.pyc'):
                os.remove(os.path.join(root, file))


def check_requirements():
    """检查依赖是否安装"""
    required = ['flask', 'graphviz', 'pandas', 'pyinstaller', 'waitress']
    missing = []

    for package in required:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)

    if missing:
        print(f"缺少依赖包: {', '.join(missing)}")
        print("正在安装依赖...")
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)

    # 检查graphviz系统安装
    try:
        import graphviz
        graphviz.version()
    except Exception as e:
        print("警告: Graphviz可能未正确安装")
        print("请确保Graphviz已安装并添加到系统PATH")
        print("下载地址: https://graphviz.org/download/")


def create_demo_folder():
    """创建演示程序文件夹"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    demo_folder = f"LR0_文法分析器_演示版_{timestamp}"

    if not os.path.exists(demo_folder):
        os.makedirs(demo_folder)

    return demo_folder


def copy_files_to_demo(demo_folder):
    """复制文件到演示程序文件夹"""
    # 复制exe文件
    if os.path.exists('dist/LR0_Analyzer.exe'):
        shutil.copy('dist/LR0_Analyzer.exe',
                    os.path.join(demo_folder, 'LR0_文法分析器.exe'))
        print("已复制: LR0_文法分析器.exe")

    # 创建使用说明
    create_readme(demo_folder)

    # 复制必要的dll文件（如果有）
    if os.path.exists('dist'):
        for file in os.listdir('dist'):
            if file.endswith('.dll'):
                shutil.copy(os.path.join('dist', file),
                            os.path.join(demo_folder, file))


def create_readme(demo_folder):
    """创建使用说明文档"""
    readme_content = f"""LR(0) 文法分析器 - 演示程序使用说明
{'=' * 60}

【程序信息】
版本: 1.0
编译日期: {datetime.now().strftime("%Y-%m-%d")}
类型: LR(0)文法分析Web应用

【运行要求】
1. 操作系统: Windows 7/10/11 (64位)
2. 内存: 至少2GB可用内存
3. 磁盘空间: 至少100MB可用空间
4. 需要安装: Microsoft Visual C++ Redistributable
   (如未安装，请从微软官网下载安装)

【安装步骤】
1. 解压整个文件夹到任意位置（建议不要在C盘根目录）
2. 双击运行 "LR0_文法分析器.exe"
3. 首次运行可能会被Windows Defender拦截，请点击"更多信息"->"仍要运行"

【使用步骤】
1. 启动程序后，会自动打开浏览器访问 http://localhost:5000
2. 如果浏览器未自动打开，请手动输入上述地址
3. 在页面左侧输入文法规则
   - 每行一个产生式
   - 使用 '->' 或 '=' 分隔左右部
   - 空串用 '@' 表示
4. 输入测试字符串（每行一个）
5. 点击"开始分析"按钮
6. 在右侧查看分析结果：
   - 文法规则
   - DFA状态图
   - LR(0)分析表
   - 输入串分析过程

【示例文法】
1. 简单文法:
   S -> a A | b B
   A -> c A | d
   B -> c B | d

2. 表达式文法:
   S -> E
   E -> ( E + E ) | ( E * E ) | +

3. 带空串文法:
   A -> a A b | a A d | @

【注意事项】
1. 请勿删除程序所在目录的任何文件
2. 程序运行时会在后台启动Web服务器
3. 关闭控制台窗口会停止程序
4. 如果需要生成DFA图，请确保已安装Graphviz
   （非必需，但无Graphviz无法生成图片）

【常见问题】
1. 程序闪退？
   → 可能是缺少VC++运行库，请安装VC_redist.x64.exe

2. 无法生成DFA图？
   → 请安装Graphviz并添加到系统PATH
     下载地址: https://graphviz.org/download/

3. 浏览器无法访问？
   → 检查防火墙设置，或尝试使用其他浏览器
   → 手动访问: http://127.0.0.1:5000

4. 程序无法启动？
   → 以管理员身份运行
   → 关闭杀毒软件后重试

【技术支持】
如有问题，请联系开发者或查看程序控制台输出的错误信息

【版权声明】
本程序仅供学习和演示使用，请勿用于商业用途
{'=' * 60}
"""

    with open(os.path.join(demo_folder, '使用说明.txt'), 'w', encoding='utf-8') as f:
        f.write(readme_content)

    print("已创建: 使用说明.txt")


def main():
    print("=" * 60)
    print("LR(0) 文法分析器 - 打包工具")
    print("=" * 60)

    # 1. 清理
    print("\n[1/5] 清理旧文件...")
    clean_build()

    # 2. 检查依赖
    print("\n[2/5] 检查依赖包...")
    check_requirements()

    # 3. 打包
    print("\n[3/5] 开始打包...")
    try:
        # 使用PyInstaller打包
        cmd = [
            'pyinstaller',
            '--clean',
            '--onefile',
            '--add-data', 'templates;templates',
            '--add-data', 'static;static',
            '--add-data', 'src;src',
            '--hidden-import', 'flask',
            '--hidden-import', 'flask.cli',
            '--hidden-import', 'graphviz',
            '--hidden-import', 'pandas',
            '--hidden-import', 'waitress',
            '--hidden-import', 'src.engine',
            '--hidden-import', 'src.grammar',
            '--hidden-import', 'src.parser',
            '--hidden-import', 'src.utils',
            '--hidden-import', 'src.visualizer',
            '--exclude-module', 'matplotlib',
            '--exclude-module', 'numpy',
            '--exclude-module', 'scipy',
            '--exclude-module', 'tkinter',
            '--name', 'LR0_Analyzer',
            '--console',  # 显示控制台
            '--upx-dir', 'upx',  # 如果有UPX压缩工具
            'app.py'
        ]

        # 如果有图标文件，添加图标参数
        if os.path.exists('icon.ico'):
            cmd.extend(['--icon', 'icon.ico'])

        print(f"执行命令: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)

    except subprocess.CalledProcessError as e:
        print(f"打包失败: {e}")
        return

    # 4. 创建演示文件夹
    print("\n[4/5] 创建演示程序文件夹...")
    demo_folder = create_demo_folder()

    # 5. 复制文件
    print("\n[5/5] 复制文件...")
    copy_files_to_demo(demo_folder)

    print("\n" + "=" * 60)
    print("✅ 打包完成！")
    print(f"演示程序位于: {demo_folder}")
    print("=" * 60)
    print("\n文件夹内容:")
    for item in os.listdir(demo_folder):
        print(f"  - {item}")

    print("\n下一步:")
    print("1. 将整个文件夹复制到目标计算机")
    print("2. 运行 'LR0_文法分析器.exe'")
    print("3. 查看 '使用说明.txt' 获取详细帮助")


if __name__ == '__main__':
    main()