#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
nfcpyリーダー検出テスト
"""
import nfc

print("="*70)
print("nfcpy リーダー検出テスト")
print("="*70)

# テスト1: 単純な'usb'で検出
print("\n[テスト1] ContactlessFrontend('usb')")
try:
    clf = nfc.ContactlessFrontend('usb')
    if clf:
        print(f"✅ 成功: {clf}")
        clf.close()
    else:
        print("❌ 失敗: リーダーが見つかりません")
except Exception as e:
    print(f"❌ エラー: {e}")

# テスト2: usb:000 形式で検出
print("\n[テスト2] ContactlessFrontend('usb:000')")
try:
    clf = nfc.ContactlessFrontend('usb:000')
    if clf:
        print(f"✅ 成功: {clf}")
        clf.close()
    else:
        print("❌ 失敗: リーダーが見つかりません")
except Exception as e:
    print(f"❌ エラー: {e}")

# テスト3: 複数のUSBパスを試す
print("\n[テスト3] 複数のUSBパスをスキャン")
for i in range(5):
    path = f'usb:{i:03d}'
    try:
        clf = nfc.ContactlessFrontend(path)
        if clf:
            print(f"✅ {path}: 検出成功 - {clf}")
            clf.close()
    except Exception as e:
        print(f"❌ {path}: {e}")

print("\n" + "="*70)
