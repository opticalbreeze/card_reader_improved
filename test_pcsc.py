#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PC/SCリーダーテスト
"""
try:
    from smartcard.System import readers as pcsc_readers
    PYSCARD_AVAILABLE = True
except ImportError:
    PYSCARD_AVAILABLE = False
    print("❌ pyscard がインストールされていません")
    exit(1)

print("="*70)
print("PC/SC リーダーテスト")
print("="*70)

if PYSCARD_AVAILABLE:
    try:
        reader_list = pcsc_readers()
        print(f"\n✅ PC/SCリーダー検出: {len(reader_list)}台\n")
        
        for i, reader in enumerate(reader_list, 1):
            print(f"  {i}. {reader}")
        
        if len(reader_list) == 0:
            print("⚠️  PC/SCリーダーが見つかりません")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "="*70)
