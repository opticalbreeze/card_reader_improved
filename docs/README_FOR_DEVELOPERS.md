# 開発者向けREADME

このドキュメントは、プロジェクトに参加する開発者向けの包括的なガイドです。

---

## 🎯 プロジェクトの目的

ICカードリーダーを使った勤怠打刻システムです。WindowsとRaspberry Piの両方に対応しています。

---

## 📁 プロジェクト構造の理解

### 主要ファイル

| ファイル | 説明 | 環境 |
|---------|------|------|
| `pi_client.py` | Raspberry Pi版クライアント（統合版） | Raspberry Pi |
| `pi_client_simple.py` | Raspberry Pi版クライアント（シンプル版） | Raspberry Pi |
| `win_client.py` | Windows版クライアント | Windows |
| `common_utils.py` | 共通ユーティリティ関数 | 両方 |
| `constants.py` | 定数定義 | 両方 |
| `gpio_config.py` | GPIO設定 | Raspberry Pi |

### モジュールの依存関係

```
pi_client.py / win_client.py
    ├── common_utils.py
    │   └── constants.py
    ├── constants.py
    └── gpio_config.py (Raspberry Piのみ)
```

---

## 🔑 重要な設計原則

### 1. **環境分離**

Windows用とRaspberry Pi用は完全に分離されています。

**理由**: 
- 環境依存ライブラリの競合を避ける
- エラーハンドリングを簡潔にする
- 保守性を向上させる

詳細は [Windows用とRaspberry Pi用を分離した理由](WHY_SEPARATE_WINDOWS_AND_RASPBERRY_PI.md) を参照。

### 2. **定数の集約**

すべてのハードコーディングされた値は`constants.py`に定義されています。

**例**:
```python
# ❌ 悪い例
time.sleep(600)

# ✅ 良い例
from constants import DEFAULT_RETRY_INTERVAL
time.sleep(DEFAULT_RETRY_INTERVAL)
```

### 3. **共通関数の集約**

重複する関数は`common_utils.py`に集約されています。

**例**:
- `get_mac_address()` - MACアドレス取得
- `load_config()` - 設定ファイル読み込み
- `send_attendance_to_server()` - サーバーへのデータ送信

---

## 🛠️ 開発環境のセットアップ

### 必要なツール

- Python 3.7以上
- Git
- テキストエディタ（VSCode推奨）

### 開発用の依存関係

```bash
# Raspberry Pi版
pip install -r requirements_unified.txt

# Windows版
pip install -r requirements_windows.txt
```

---

## 📝 コードを書く際の注意事項

### 1. **新しい機能を追加する場合**

1. 定数が必要な場合は`constants.py`に追加
2. 共通関数が必要な場合は`common_utils.py`に追加
3. 環境固有の機能は適切なファイルに追加

### 2. **バグを修正する場合**

1. 問題の原因を特定
2. 最小限の変更で修正
3. エラーハンドリングを追加（必要に応じて）
4. ドキュメントを更新

### 3. **リファクタリングする場合**

1. 重複コードを特定
2. 共通関数として抽出
3. 既存のテストが動作することを確認
4. ドキュメントを更新

---

## 🧪 テスト方法

### 手動テスト

```bash
# Raspberry Pi版
python3 pi_client.py

# Windows版
python win_client.py
```

### デバッグ

ログ出力を確認：
```bash
# サービスログ（Raspberry Pi）
sudo journalctl -u attendance-client-fixed.service -f
```

---

## 📚 ドキュメント

### 開発者向けドキュメント

- [コード構造ガイド](CODE_STRUCTURE_GUIDE.md) - コード構造の詳細
- [開発者ガイド](DEVELOPER_GUIDE.md) - コーディング規約とベストプラクティス
- [Windows用とRaspberry Pi用を分離した理由](WHY_SEPARATE_WINDOWS_AND_RASPBERRY_PI.md)
- [Raspberry Pi版クラッシュ原因の実際の分析](RASPBERRY_PI_CRASH_ANALYSIS.md)

### ユーザー向けドキュメント

- [セットアップガイド](SETUP_GUIDE.md)
- [Raspberry Pi版セットアップガイド](RASPBERRY_PI_SETUP_GUIDE.md)
- [トラブルシューティング](TROUBLESHOOTING.md)

---

## 🔄 変更履歴

主要な変更は [CHANGELOG.md](CHANGELOG.md) に記録されています。

---

## 🤝 コントリビューション

### プルリクエストの作成

1. 新しいブランチを作成
2. 変更をコミット
3. プルリクエストを作成
4. コードレビューを依頼

### コミットメッセージ

```
[種類] 簡潔な説明

詳細な説明（必要に応じて）
```

**種類**:
- `[追加]` - 新機能の追加
- `[修正]` - バグ修正
- `[改善]` - 既存機能の改善
- `[リファクタ]` - コードのリファクタリング
- `[ドキュメント]` - ドキュメントの更新

---

## ❓ よくある質問

### Q: 新しいカードリーダーを追加したい

A: `common_utils.py`の`get_pcsc_commands()`関数にリーダー名の判定を追加してください。

### Q: 設定項目を追加したい

A: `constants.py`に定数を追加し、`common_utils.py`の`load_config()`でデフォルト値を設定してください。

### Q: エラーメッセージを変更したい

A: `constants.py`のメッセージ定数を変更するか、エラーメッセージを直接修正してください。

---

## 📞 サポート

問題が発生した場合は、以下を確認してください：

1. [トラブルシューティング](TROUBLESHOOTING.md)
2. [Raspberry Pi版クラッシュ原因の実際の分析](RASPBERRY_PI_CRASH_ANALYSIS.md)
3. ログファイルの内容

---

## 🎯 まとめ

このプロジェクトでは、以下の原則に従って開発します：

1. ✅ **DRY原則**: 重複コードを避ける
2. ✅ **定数の集約**: ハードコーディングを避ける
3. ✅ **環境分離**: Windows用とRaspberry Pi用を分離
4. ✅ **安全なエラーハンドリング**: オプション機能の失敗時にクラッシュさせない
5. ✅ **明確なドキュメント**: 型ヒントとdocstringでコードを説明

これらの原則に従うことで、保守性が高く、理解しやすいコードを維持できます。

