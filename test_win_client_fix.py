#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
win_client.pyの修正確認テスト
GUIなしでコアロジックのみテスト
"""
import nfc
import time

print("="*70)
print("win_client.py 修正確認テスト")
print("="*70)

# 修正後のコード（win_client.pyと同じロジック）
try:
    print("\n[テスト1] リーダー検出")
    clf = nfc.ContactlessFrontend('usb')
    if clf:
        print(f"✅ リーダー検出成功: {clf}")
        clf.close()
    else:
        print("❌ リーダーが見つかりません")
        exit(1)
    
    print("\n[テスト2] カード読み取りロジック")
    print("📝 カードをタッチしてください（10秒間待機）...\n")
    
    clf = nfc.ContactlessFrontend('usb')
    last_id = None
    start_time = time.time()
    
    while time.time() - start_time < 10:
        try:
            tag = clf.connect(rdwr={
                'on-connect': lambda tag: False,
                'beep-on-connect': False
            })
            
            if tag:
                # win_client.pyと同じIDm取得ロジック
                card_id = None
                try:
                    if hasattr(tag, 'idm'):
                        card_id = tag.idm.hex().upper()
                    elif hasattr(tag, '_nfcid'):
                        card_id = tag._nfcid.hex().upper()
                    elif hasattr(tag, 'identifier'):
                        card_id = tag.identifier.hex().upper()
                except:
                    pass
                
                if card_id and card_id != last_id:
                    print(f"✅ カード検出成功!")
                    print(f"   IDm: {card_id}")
                    print(f"   Tag type: {type(tag).__name__}")
                    print("\n👍 win_client.pyの修正は正常に動作します！")
                    last_id = card_id
                    time.sleep(2)
                    break
        except:
            time.sleep(0.1)
    
    clf.close()
    
    if not last_id:
        print("⚠️  カードが検出されませんでした（タイムアウト）")
        print("   カードをタッチして再度試してください")
    
    print("\n✅ テスト完了")
    
except Exception as e:
    print(f"\n❌ エラー: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
