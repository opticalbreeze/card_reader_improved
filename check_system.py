#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
システム診断ツール
カードリーダーシステムの状態をチェックし、問題があれば解決方法を提示
"""

import sys
import subprocess
import os
from pathlib import Path

class SystemChecker:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.passed = []
    
    def run_command(self, cmd):
        """コマンドを実行して結果を取得"""
        try:
            result = subprocess.run(
                cmd, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)
    
    def check_python_version(self):
        """Python バージョン確認"""
        print("□ Pythonバージョン確認...", end=" ")
        version = sys.version_info
        if version.major == 3 and version.minor >= 7:
            print("✓ OK")
            self.passed.append(f"Python {version.major}.{version.minor}.{version.micro}")
            return True
        else:
            print("✗ NG")
            self.issues.append({
                'name': 'Pythonバージョンが古い',
                'detail': f'Python {version.major}.{version.minor}が検出されました',
                'solution': 'Python 3.7以上が必要です。システムをアップデートしてください。'
            })
            return False
    
    def check_i2c_enabled(self):
        """I2C有効化確認"""
        print("□ I2C設定確認...", end=" ")
        success, stdout, _ = self.run_command("ls /dev/i2c-* 2>/dev/null")
        if success and '/dev/i2c-' in stdout:
            print("✓ OK")
            self.passed.append("I2Cデバイスが有効")
            return True
        else:
            print("✗ NG")
            self.issues.append({
                'name': 'I2Cが無効',
                'detail': '/dev/i2c-1が見つかりません',
                'solution': 'sudo raspi-config で I2C を有効にしてください\n       または: sudo sh -c "echo dtparam=i2c_arm=on >> /boot/config.txt" && sudo reboot'
            })
            return False
    
    def check_python_libraries(self):
        """Pythonライブラリ確認"""
        print("□ Pythonライブラリ確認...")
        libraries = {
            'nfcpy': 'nfc',
            'pyscard': 'smartcard',
            'smbus2': 'smbus2',
            'requests': 'requests',
            'RPi.GPIO': 'RPi.GPIO'
        }
        
        all_ok = True
        for name, module in libraries.items():
            try:
                __import__(module)
                print(f"  ✓ {name}")
                self.passed.append(f"{name}ライブラリ")
            except ImportError:
                print(f"  ✗ {name}")
                self.issues.append({
                    'name': f'{name}ライブラリ未インストール',
                    'detail': f'{name}が見つかりません',
                    'solution': f'pip install {name}'
                })
                all_ok = False
        
        return all_ok
    
    def check_pcscd_service(self):
        """PC/SCサービス確認"""
        print("□ PC/SCサービス確認...", end=" ")
        success, stdout, _ = self.run_command("systemctl is-active pcscd")
        if 'active' in stdout:
            print("✓ OK")
            self.passed.append("PC/SCサービス起動中")
            return True
        else:
            print("✗ NG")
            self.issues.append({
                'name': 'PC/SCサービスが起動していない',
                'detail': 'pcscdデーモンが停止しています',
                'solution': 'sudo systemctl start pcscd\n       自動起動設定: sudo systemctl enable pcscd'
            })
            return False
    
    def check_card_readers(self):
        """カードリーダー検出確認"""
        print("□ カードリーダー検出...")
        
        # USBデバイス確認
        success, stdout, _ = self.run_command("lsusb")
        if '054c:06c1' in stdout or 'Sony' in stdout:
            print("  ✓ Sony RC-S380/S検出")
            self.passed.append("Sony RC-S380/S USB接続")
        else:
            print("  ! カードリーダーがUSBに接続されていません")
            self.warnings.append({
                'name': 'カードリーダー未接続',
                'detail': 'USBポートにカードリーダーが見つかりません',
                'solution': 'カードリーダーをUSBポートに接続してください'
            })
            return False
        
        # nfcpy確認
        try:
            import nfc
            try:
                clf = nfc.ContactlessFrontend('usb')
                if clf:
                    print(f"  ✓ nfcpyで検出: {clf}")
                    clf.close()
                    self.passed.append("nfcpyでリーダー検出")
                else:
                    print("  ✗ nfcpyでリーダーを開けません")
            except Exception as e:
                print(f"  ✗ nfcpyエラー: {e}")
                self.issues.append({
                    'name': 'nfcpyアクセスエラー',
                    'detail': str(e),
                    'solution': 'udevルールを設定してください:\n       sudo ./setup.sh を実行'
                })
        except ImportError:
            pass
        
        return True
    
    def check_config_file(self):
        """設定ファイル確認"""
        print("□ 設定ファイル確認...", end=" ")
        if Path('client_config.json').exists():
            print("✓ OK")
            self.passed.append("client_config.json存在")
            return True
        else:
            print("! 警告")
            self.warnings.append({
                'name': '設定ファイルが見つかりません',
                'detail': 'client_config.jsonが存在しません',
                'solution': 'プログラムを一度起動すると自動作成されます\n       または: cp client_config_sample.json client_config.json'
            })
            return False
    
    def check_lcd(self):
        """LCD接続確認"""
        print("□ LCDディスプレイ確認...", end=" ")
        success, stdout, _ = self.run_command("i2cdetect -y 1 2>/dev/null | grep -E '27|3f'")
        if success and ('27' in stdout or '3f' in stdout):
            print("✓ OK")
            self.passed.append("LCD (I2C 0x27または0x3F)")
            return True
        else:
            print("! 警告")
            self.warnings.append({
                'name': 'LCDが検出されません',
                'detail': 'I2Cアドレス 0x27 または 0x3F にLCDが見つかりません',
                'solution': 'LCD接続を確認してください（オプション機能）'
            })
            return False
    
    def print_summary(self):
        """結果サマリー表示"""
        print("\n" + "="*70)
        print("診断結果サマリー")
        print("="*70)
        
        if self.passed:
            print(f"\n✓ 正常 ({len(self.passed)}件):")
            for item in self.passed:
                print(f"  • {item}")
        
        if self.warnings:
            print(f"\n! 警告 ({len(self.warnings)}件):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"\n  {i}. {warning['name']}")
                print(f"     詳細: {warning['detail']}")
                print(f"     対処: {warning['solution']}")
        
        if self.issues:
            print(f"\n✗ エラー ({len(self.issues)}件):")
            for i, issue in enumerate(self.issues, 1):
                print(f"\n  {i}. {issue['name']}")
                print(f"     詳細: {issue['detail']}")
                print(f"     対処: {issue['solution']}")
        
        print("\n" + "="*70)
        
        if not self.issues:
            print("結果: システムは正常です！プログラムを起動できます。")
        else:
            print(f"結果: {len(self.issues)}個の問題があります。上記の対処方法を実行してください。")
        
        print("="*70 + "\n")
        
        return len(self.issues) == 0

def main():
    print("="*70)
    print("  カードリーダーシステム 診断ツール")
    print("="*70)
    print("システムの状態をチェックしています...\n")
    
    checker = SystemChecker()
    
    # 各項目をチェック
    checker.check_python_version()
    checker.check_i2c_enabled()
    checker.check_python_libraries()
    checker.check_pcscd_service()
    checker.check_card_readers()
    checker.check_config_file()
    checker.check_lcd()
    
    # サマリー表示
    all_ok = checker.print_summary()
    
    if all_ok:
        print("プログラムを起動するには:")
        print("  python3 client_card_reader_unified_improved.py")
        print("")
        sys.exit(0)
    else:
        print("問題を解決してから、もう一度診断を実行してください:")
        print("  python3 check_system.py")
        print("")
        sys.exit(1)

if __name__ == "__main__":
    main()

