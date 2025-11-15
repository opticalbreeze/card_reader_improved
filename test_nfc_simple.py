#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
nfcpy簡易テスト（AI_TROUBLESHOOTING_GUIDEに基づく）
"""
import nfc
import binascii

print("="*70)
print("nfcpy 簡易テスト")
print("="*70)

try:
    # ガイドの推奨方法: 'usb' のみを指定
    print("\n[テスト1] ContactlessFrontend('usb') で接続を試みます...")
    clf = nfc.ContactlessFrontend('usb')
    
    if clf:
        print("✅ リーダー接続成功!")
        print(f"   リーダー: {clf}")
        print("\n📝 カードをタッチしてください（10秒待機）...")
        
        def on_connect(tag):
            try:
                # IDmを取得
                if hasattr(tag, 'idm'):
                    idm = binascii.hexlify(tag.idm).decode('utf-8').upper()
                elif hasattr(tag, '_nfcid'):
                    idm = binascii.hexlify(tag._nfcid).decode('utf-8').upper()
                elif hasattr(tag, 'identifier'):
                    idm = binascii.hexlify(tag.identifier).decode('utf-8').upper()
                else:
                    idm = "不明"
                
                print(f"\n✅ カード検出成功!")
                print(f"   IDm: {idm}")
                print(f"   Tag type: {type(tag)}")
                print(f"   Tag: {tag}")
                return True
            except Exception as e:
                print(f"\n❌ カード情報取得エラー: {e}")
                import traceback
                traceback.print_exc()
                return False
        
        clf.connect(rdwr={'on-connect': on_connect, 'beep-on-connect': False})
        clf.close()
        print("\n✅ テスト完了")
    else:
        print("❌ リーダーが見つかりません")
        
except Exception as e:
    print(f"\n❌ エラー: {e}")
    import traceback
    traceback.print_exc()
    print("\n💡 ヒント:")
    print("  - RC-S380がUSB接続されているか確認してください")
    print("  - NFCポートソフトウェアがインストールされているか確認してください")
    print("  - 他のアプリケーションがリーダーを使用していないか確認してください")

print("\n" + "="*70)
