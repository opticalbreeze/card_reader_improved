#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
両方のリーダー検出テスト（修正確認）
"""
import nfc
from smartcard.System import readers as pcsc_readers

print("="*70)
print("両方のリーダー検出テスト")
print("="*70)

nfcpy_count = 0
pcsc_count = 0

# nfcpy検出
print("\n[1] nfcpyリーダー検出")
try:
    clf = nfc.ContactlessFrontend('usb')
    if clf:
        nfcpy_count = 1
        print(f"   ✅ nfcpyリーダー: {clf}")
        clf.close()
except Exception as e:
    print(f"   ❌ nfcpyリーダー未検出: {e}")

# PC/SC検出
print("\n[2] PC/SCリーダー検出")
try:
    reader_list = pcsc_readers()
    pcsc_count = len(reader_list)
    print(f"   ✅ PC/SCリーダー: {pcsc_count}台")
    for i, reader in enumerate(reader_list, 1):
        reader_idx = nfcpy_count + i
        print(f"      #{reader_idx}: {reader}")
except Exception as e:
    print(f"   ❌ PC/SCリーダー未検出: {e}")

# 結果サマリー
print("\n" + "="*70)
print(f"検出結果: nfcpy:{nfcpy_count}台 / PC/SC:{pcsc_count}台")
print(f"合計: {nfcpy_count + pcsc_count}台")
print("="*70)

if nfcpy_count > 0 and pcsc_count > 0:
    print("\n✅ 両方のリーダーが正常に検出されました！")
else:
    print("\n⚠️  一部のリーダーが検出されませんでした")
