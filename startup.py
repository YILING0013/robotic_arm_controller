#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动脚本 - 检查依赖并启动主程序
"""

import sys
import os
import platform

def check_requirements():
    """检查所有必需的依赖包"""
    print("正在检查依赖包...")
    required_packages = {
        'numpy': 'numpy',
        'matplotlib': 'matplotlib', 
        'serial': 'pyserial',
        'ikpy': 'ikpy',
        'ttkbootstrap': 'ttkbootstrap'  # 新增依赖
    }
    
    missing_packages = []
    
    for package, install_name in required_packages.items():
        try:
            __import__(package)
            print(f"  - {package}: [OK]")
        except ImportError:
            missing_packages.append(install_name)
            print(f"  - {package}: [缺失]")
    
    if missing_packages:
        print("\n❌ 缺少必需的依赖包:")
        for pkg in missing_packages:
            print(f"   - {pkg}")
        print("\n请运行以下命令安装:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    print("\n✅ 所有依赖包检查通过!")
    return True

def main():
    """主函数"""
    print("=" * 60)
    print("🤖 5DOF机械臂上位机 v2.1 (UI优化版)")
    print("=" * 60)
    
    # 1. 检查依赖
    if not check_requirements():
        input("\n按回车键退出...")
        return
    
    # 2. 启动主程序
    print("\n🚀 正在启动主程序...")
    try:
        # 将当前目录添加到系统路径，以确保模块可以被找到
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
            
        from main import main as main_app
        main_app()
    except ImportError as e:
        print(f"\n❌ 导入主程序模块失败: {e}")
        print("请确保所有 .py 文件都在同一个目录下。")
        input("\n按回车键退出...")
    except Exception as e:
        print(f"\n❌ 启动主程序时发生未知错误: {e}")
        import traceback
        traceback.print_exc()
        input("\n按回车键退出...")

if __name__ == "__main__":
    main()
