#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动脚本 - 字体配置和程序启动
"""

import sys
import os
import platform

def check_requirements():
    """检查依赖包"""
    required_packages = {
        'numpy': 'numpy',
        'matplotlib': 'matplotlib', 
        'serial': 'pyserial',
        'ikpy': 'ikpy'
    }
    
    missing_packages = []
    
    for package, install_name in required_packages.items():
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(install_name)
    
    if missing_packages:
        print("❌ 缺少必需的依赖包:")
        for pkg in missing_packages:
            print(f"   - {pkg}")
        print("\n请运行以下命令安装:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ 所有依赖包检查通过")
    return True

def font_setup_wizard():
    """字体设置向导"""
    print("\n" + "="*60)
    print("🎨 字体配置向导")
    print("="*60)
    
    system = platform.system()
    print(f"检测到操作系统: {system}")
    
    # 根据系统推荐字体
    if system == "Windows":
        recommended_fonts = [
            ("Microsoft YaHei UI", "微软雅黑UI（推荐）"),
            ("Microsoft YaHei", "微软雅黑"),
            ("SimHei", "黑体"),
            ("SimSun", "宋体")
        ]
    elif system == "Darwin":  # macOS
        recommended_fonts = [
            ("PingFang SC", "苹方-简（推荐）"),
            ("Hiragino Sans GB", "冬青黑体-简"),
            ("STHeiti", "华文黑体"),
            ("Arial Unicode MS", "Arial Unicode MS")
        ]
    else:  # Linux
        recommended_fonts = [
            ("Noto Sans CJK SC", "思源黑体-简（推荐）"),
            ("WenQuanYi Micro Hei", "文泉驿微米黑"),
            ("Droid Sans Fallback", "Droid Sans Fallback"),
            ("DejaVu Sans", "DejaVu Sans")
        ]
    
    print("\n推荐字体:")
    for i, (font_name, description) in enumerate(recommended_fonts, 1):
        print(f"{i}. {description}")
    
    print(f"{len(recommended_fonts) + 1}. 自动检测最佳字体")
    print(f"{len(recommended_fonts) + 2}. 跳过字体配置")
    
    try:
        while True:
            choice = input(f"\n请选择字体 (1-{len(recommended_fonts) + 2}): ").strip()
            
            if choice.isdigit():
                choice_num = int(choice)
                if 1 <= choice_num <= len(recommended_fonts):
                    selected_font = recommended_fonts[choice_num - 1][0]
                    print(f"✅ 已选择字体: {selected_font}")
                    
                    # 更新配置文件
                    update_font_config(selected_font)
                    return True
                    
                elif choice_num == len(recommended_fonts) + 1:
                    print("🔍 将自动检测最佳字体...")
                    return True
                    
                elif choice_num == len(recommended_fonts) + 2:
                    print("⏭️ 跳过字体配置，使用默认设置")
                    return True
            
            print("❌ 无效选择，请重新输入")
            
    except KeyboardInterrupt:
        print("\n⏹️ 用户取消，使用默认字体设置")
        return True

def update_font_config(font_name):
    """更新字体配置"""
    try:
        # 读取配置文件
        config_file = "config.py"
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 替换字体配置
            import re
            pattern = r"'font_family':\s*'[^']*'"
            replacement = f"'font_family': '{font_name}'"
            
            new_content = re.sub(pattern, replacement, content)
            
            # 写回文件
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"✅ 字体配置已更新: {font_name}")
            
    except Exception as e:
        print(f"⚠️ 更新字体配置失败: {e}")

def main():
    """主函数"""
    print("5DOF机械臂上位机")
    print("=" * 60)
    
    # 检查依赖
    if not check_requirements():
        input("\n按回车键退出...")
        return
    
    # 字体配置向导
    try:
        setup_complete = font_setup_wizard()
        if not setup_complete:
            return
    except Exception as e:
        print(f"⚠️ 字体配置过程中出现错误: {e}")
        print("将使用默认字体设置")
    
    # 启动主程序
    print("\n🚀 正在启动主程序...")
    try:
        from main import main as main_app
        main_app()
    except Exception as e:
        print(f"❌ 启动主程序失败: {e}")
        input("\n按回车键退出...")

if __name__ == "__main__":
    main()