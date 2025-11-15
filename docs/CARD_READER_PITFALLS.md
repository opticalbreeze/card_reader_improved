# カードリーダー開発の落とし穴

## 概要
このドキュメントは、カードリーダーシステムの開発中に遭遇した問題と解決策をまとめたものです。同様のシステムを開発する際の参考にしてください。

---

## 1. nfcpyライブラリの使用方法

### ❌ 間違った実装
```python
# USBパスを手動で列挙する方法（推奨されない）
for i in range(10):
    try:
        clf = nfc.ContactlessFrontend(f'usb:{i:03d}')
        if clf:
            break
    except:
        continue
```

**問題点:**
- リーダーが`usb:001`にあるのに`usb:000`から探し始めると見つからない
- デバイス番号は環境によって変わる
- 不要なループで処理が遅くなる

### ✅ 正しい実装
```python
# ライブラリに自動検出させる方法（推奨）
clf = nfc.ContactlessFrontend('usb')
```

**理由:**
- nfcpyライブラリが自動的に利用可能なリーダーを見つける
- 環境依存がなく、どのUSBポートでも動作する
- AI_TROUBLESHOOTING_GUIDE.mdでも推奨されている方法

**参考:** `AI_TROUBLESHOOTING_GUIDE.md` - Section 3

---

## 2. PC/SCリーダーの定期チェック

### ❌ 間違った実装
```python
def periodic_reader_check(self):
    # nfcpyのみチェック
    for i in range(10):
        try:
            clf = nfc.ContactlessFrontend(f'usb:{i:03d}')
            # PC/SCリーダーのチェックなし
        except:
            pass
```

**問題点:**
- PC/SCリーダーの状態を確認していない
- リーダーインデックスの計算ミス（nfcpyとPC/SCで重複）
- 一方のリーダーしか動作しない

### ✅ 正しい実装
```python
def periodic_reader_check(self):
    # nfcpy検出
    nfcpy_count = 0
    if NFCPY_AVAILABLE:
        try:
            clf = nfc.ContactlessFrontend('usb')
            if clf:
                nfcpy_count = 1
                clf.close()
        except:
            pass
    
    # PC/SC検出（nfcpyの後からインデックスを割り当て）
    if PYSCARD_AVAILABLE:
        try:
            reader_list = pcsc_readers()
            pcsc_count = len(reader_list)
            # nfcpy_count + i + 1 でインデックスを計算
            detected_pcsc_readers = [
                (reader, nfcpy_count + i + 1) 
                for i, reader in enumerate(reader_list)
            ]
        except:
            pass
```

**理由:**
- 両方のリーダータイプを正しくチェック
- リーダー番号が重複しない（nfcpy=#1, PC/SC=#2,#3...）
- スリープ復帰後も正常に動作

---

## 3. ファイルエンコーディングの問題

### ❌ 問題のあったファイル
```
requirements_windows.txt (Shift-JIS)
# 日本語コメント - pip installでエラー
```

**エラー:**
```
UnicodeDecodeError: 'cp932' codec can't decode byte 0x83
```

### ✅ 解決策
```
requirements_windows.txt (UTF-8)
# Japanese comment - Windows client requirements
```

**理由:**
- pipはUTF-8を期待している
- Windowsのデフォルトエンコーディング（Shift-JIS/CP932）では読めない
- 国際化対応のためUTF-8を使用

---

## 4. OneDriveパスの問題

### ❌ 問題のあるパス
```
C:\Users\optic\OneDrive\デスクトップ\カード打刻\card_reader_improved
```

**問題点:**
- OneDrive同期によるパス混乱
- デスクトップに作成したファイルが見えない
- `C:\Users\optic\Desktop` と `C:\Users\optic\OneDrive\デスクトップ` の2つが存在

### ✅ 解決策
```powershell
# 実際のデスクトップパスを確認
$env:USERPROFILE\Desktop

# プロジェクトをローカルにコピー
Copy-Item -Path "OneDriveパス" -Destination "C:\Users\optic\Desktop\card_reader_improved" -Recurse
```

**理由:**
- OneDrive外に配置することで同期の影響を受けない
- バッチファイルが確実にデスクトップに表示される
- ファイルアクセスが高速化

---

## 5. バッチファイルのエンコーディング

### ❌ 問題のあるバッチファイル
```batch
@echo off
chcp 65001 >nul
cd /d "C:\Users\optic\Desktop\card_reader_improved"
# UTF-8で保存 → 文字化けエラー
```

**エラー:**
```
'd' は、内部コマンドまたは外部コマンドとして認識されていません。
```

### ✅ 正しいバッチファイル
```batch
@echo off
cd /d C:\Users\optic\Desktop\card_reader_improved
venv\Scripts\python.exe win_client.py
pause
```

**保存形式:** ASCII または Shift-JIS（日本語不使用）

**理由:**
- WindowsのバッチファイルはASCIIまたはShift-JISを期待
- UTF-8で保存すると特殊文字が誤認識される
- シンプルな英数字のみのコマンドが最も安全

---

## 6. IDm抽出の互換性

### ❌ 単一属性のみチェック
```python
if hasattr(tag, 'idm'):
    card_id = tag.idm.hex().upper()
```

**問題点:**
- カードタイプによって属性名が異なる
- 一部のカードで読み取り失敗

### ✅ 複数属性をチェック
```python
try:
    if hasattr(tag, 'idm'):
        card_id = tag.idm.hex().upper()
    elif hasattr(tag, '_nfcid'):
        card_id = tag._nfcid.hex().upper()
    elif hasattr(tag, 'identifier'):
        card_id = tag.identifier.hex().upper()
    else:
        card_id = None
except:
    card_id = None
```

**理由:**
- FeliCa: `tag.idm`
- MIFARE: `tag.identifier`
- その他NFC: `tag._nfcid`
- 様々なカードタイプに対応

---

## 7. スリープ復帰対応

### ❌ 初期化のみ実装
```python
def monitor_readers(self):
    clf = nfc.ContactlessFrontend('usb')
    # 一度だけ初期化 → スリープ後に動作しない
```

**問題点:**
- PCがスリープから復帰するとUSBデバイスが切断される
- リーダーオブジェクトが無効になる
- 手動で再起動が必要

### ✅ 定期的な再検出
```python
def periodic_reader_check(self):
    """30秒ごとにリーダーの状態をチェック"""
    while self.running:
        time.sleep(5)
        if time.time() - last_check_time >= 30:
            # リーダー数をカウント
            total_readers = detect_all_readers()
            
            if total_readers != last_reader_count:
                # リーダー数が変化 → 再起動
                self.restart_reader_monitoring()
```

**理由:**
- スリープ復帰を自動検出
- リーダー切断/再接続に自動対応
- ユーザー操作不要で復旧

---

## 8. 連続エラー時の再初期化

### ❌ エラーを無視
```python
while self.running:
    try:
        tag = clf.connect(...)
    except Exception:
        pass  # エラーを無視 → リーダー切断を検出できない
```

### ✅ エラーカウントと再初期化
```python
consecutive_errors = 0
max_consecutive_errors = 10

while self.running:
    try:
        tag = clf.connect(...)
        consecutive_errors = 0  # 成功したらリセット
    except Exception as e:
        consecutive_errors += 1
        
        if consecutive_errors >= max_consecutive_errors:
            # リーダー切断の可能性 → 再初期化
            clf.close()
            clf = nfc.ContactlessFrontend('usb')
            consecutive_errors = 0
```

**理由:**
- 一時的なエラーと切断を区別
- 自動復旧機能
- システムの堅牢性向上

---

## 9. 無効なカードIDのフィルタリング

### ❌ すべてのIDを受け入れる
```python
card_id = ''.join([f'{b:02X}' for b in response])
# 0000000000000000 も処理してしまう
```

### ✅ 無効なIDを除外
```python
INVALID_CARD_IDS = [
    '00000000',
    'FFFFFFFF',
    '0000000000000000',
    'FFFFFFFFFFFFFFFF',
]

def is_valid_card_id(card_id):
    """無効なカードIDをフィルタリング"""
    if not card_id or len(card_id) < 8:
        return False
    if card_id in INVALID_CARD_IDS:
        return False
    if card_id.startswith('00000000'):
        return False
    return True
```

**理由:**
- ダミーカードや読み取りエラーを除外
- サーバーへの無駄なリクエストを削減
- データの品質向上

---

## 10. リトライ間隔の動的変更

### ❌ 固定間隔
```python
def retry_worker(self):
    while self.running:
        time.sleep(600)  # 常に10分
        retry_pending_records()
```

**問題点:**
- ユーザーが設定を変更しても反映されない
- プログラム再起動が必要

### ✅ 動的チェック
```python
def retry_worker(self):
    last_retry_time = 0
    
    while self.running:
        time.sleep(10)  # 短い間隔でチェック
        
        elapsed = time.time() - last_retry_time
        if elapsed >= self.retry_interval:  # 設定値を参照
            last_retry_time = time.time()
            retry_pending_records()
```

**理由:**
- 設定変更が即座に反映
- ユーザビリティ向上
- 再起動不要

---

## まとめ

### 重要な教訓

1. **ライブラリの推奨方法を使う**
   - 低レベル実装よりもライブラリの高レベルAPIを信頼する

2. **複数のリーダータイプに対応**
   - nfcpyとPC/SCの両方をサポート
   - インデックス計算に注意

3. **エンコーディングに注意**
   - UTF-8を基本とする
   - Windowsバッチファイルは例外（ASCII推奨）

4. **自動復旧機能を実装**
   - スリープ復帰対応
   - エラーからの自動回復

5. **データ品質の確保**
   - 無効なIDをフィルタリング
   - 重複チェック

6. **ユーザビリティ重視**
   - 設定の動的反映
   - わかりやすいエラーメッセージ

---

## 参考資料

- `AI_TROUBLESHOOTING_GUIDE.md` - nfcpyの推奨実装方法
- `TROUBLESHOOTING.md` - 一般的なトラブルシューティング
- `PCSC_AUTOSTART_ISSUE_ANALYSIS.md` - PC/SC関連の問題解析

---

**作成日:** 2025年11月15日  
**更新日:** 2025年11月15日
