#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
nfcpyカード読み取りテスト（修正版）
AI_TROUBLESHOOTING_GUIDEに基づく実装
"""
import nfc
import time

print("="*70)
print("nfcpy カード読み取りテスト")
print("="*70)

try:
    # AI_TROUBLESHOOTING_GUIDEの推奨方法
    clf = nfc.ContactlessFrontend('usb')
    print(f"\n✅ リーダー接続成功: {clf}")
    print("\n📝 カードをタッチしてください（30秒間待機）...\n")
    
    card_count = 0
    last_id = None
    start_time = time.time()
    
    while time.time() - start_time < 30:
        try:
            # カード検出
            tag = clf.connect(rdwr={'on-connect': lambda tag: False})
            
            if tag:
                # IDmを取得
                card_id = None
                if hasattr(tag, 'idm'):
                    card_id = tag.idm.hex().upper()
                elif hasattr(tag, '_nfcid'):
                    card_id = tag._nfcid.hex().upper()
                elif hasattr(tag, 'identifier'):
                    card_id = tag.identifier.hex().upper()
                
                if card_id and card_id != last_id:
                    card_count += 1
                    print(f"✅ カード#{card_count} 検出!")
                    print(f"   IDm: {card_id}")
                    print(f"   Tag type: {type(tag).__name__}")
                    print(f"   時刻: {time.strftime('%H:%M:%S')}")
                    print()
                    last_id = card_id
                    
                    # 2秒待機してから次のカードを待つ
                    time.sleep(2)
                    last_id = None
        except Exception as e:
            # カードなし、またはタイムアウト
            time.sleep(0.1)
    
    clf.close()
    print(f"\n✅ テスト完了（読み取り枚数: {card_count}枚）")
    
except Exception as e:
    print(f"\n❌ エラー: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
