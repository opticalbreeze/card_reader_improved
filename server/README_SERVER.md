# 打刻システム - サーバー側README

## 📂 ファイル構成

```
C:\Users\take_me_hospital\Desktop\N100\
├── server.py                     ★ Flaskサーバー本体
├── requirements_server.txt       依存パッケージ
├── templates/
│   ├── index.html               トップページ
│   └── search.html              検索ページ
│
├── Dockerfile                    Docker設定
├── docker-compose.yml            Docker Compose設定
├── .dockerignore                 Docker除外ファイル
│
├── start_server.bat              通常版起動スクリプト
├── start_docker.bat              Docker版起動スクリプト
├── stop_docker.bat               Docker版停止スクリプト
│
├── DOCKER_GUIDE.md               Docker詳細ガイド
├── README_SERVER.md              このファイル
│
└── attendance.db                 データベース（自動生成）
```

---

## 🚀 起動方法

### 方法1: Docker版（推奨）

**メリット:**
- ✅ Pythonのインストール不要
- ✅ パッケージ管理不要
- ✅ 環境依存のトラブルなし

**起動:**
```cmd
start_docker.bat をダブルクリック
```

または

```bash
docker-compose up -d
```

**詳細:** `DOCKER_GUIDE.md` を参照

---

### 方法2: 通常版（Python直接実行）

**必要なもの:**
- Python 3.7以上

**セットアップ:**
```bash
pip install flask
```

**起動:**
```cmd
start_server.bat をダブルクリック
```

または

```bash
python server.py
```

---

## 🌐 アクセス

サーバーが起動したら：

```
http://192.168.1.31:5000    (ネットワーク内からアクセス)
http://localhost:5000        (サーバー自身からアクセス)
```

---

## 📊 API エンドポイント

### 1. ヘルスチェック
```
GET /api/health
```

### 2. 打刻データ受信
```
POST /api/attendance
Content-Type: application/json

{
  "idm": "012E447C1234ABCD",
  "timestamp": "2025-01-15T09:30:45",
  "terminal_id": "AA:BB:CC:DD:EE:FF"
}
```

### 3. データ検索
```
GET /api/search?idm=012E&start_date=2025-01-01&end_date=2025-01-31
```

### 4. 統計情報
```
GET /api/stats
```

詳細は `SYSTEM_OVERVIEW.md` を参照

---

## 🗄️ データベース

### ファイル
```
attendance.db
```

### テーブル構造
```sql
CREATE TABLE attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    idm TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    terminal_id TEXT NOT NULL,
    received_at TEXT NOT NULL
);
```

### バックアップ

**Windows:**
```cmd
copy attendance.db attendance_backup_%date:~0,4%%date:~5,2%%date:~8,2%.db
```

**Linux/Mac:**
```bash
cp attendance.db attendance_backup_$(date +%Y%m%d).db
```

---

## 🔧 設定変更

### ポート番号の変更

#### Docker版
`docker-compose.yml` を編集：
```yaml
ports:
  - "5001:5000"  # 左側を変更
```

#### 通常版
`server.py` の最終行を編集：
```python
app.run(host='0.0.0.0', port=5001, debug=False)
```

---

## 🐛 トラブルシューティング

### Docker版

**ポート5000が使用中:**
```bash
# 使用中のプロセス確認
netstat -ano | findstr :5000

# ポート番号を変更（docker-compose.yml編集）
```

**コンテナが起動しない:**
```bash
# ログ確認
docker-compose logs

# 再作成
docker-compose down
docker-compose up -d --force-recreate
```

### 通常版

**Flaskがインストールされていない:**
```bash
pip install flask
```

**ポート5000が使用中:**
```bash
# ポート番号を変更（server.py編集）
```

---

## 📈 パフォーマンス

### 推奨スペック
- CPU: 2コア以上
- RAM: 1GB以上
- ディスク: 5GB以上

### 同時接続数
- 最大: 100クライアント（目安）
- 推奨: 10-20クライアント

---

## 🔐 セキュリティ

### 現在の実装（試作版）
- ⚠️ 認証なし
- ⚠️ HTTP通信
- ✅ SQLインジェクション対策済み

### 本番環境推奨
1. HTTPS化
2. 認証機能の追加
3. ファイアウォール設定
4. アクセスログ記録

---

## 📝 ログ

### Docker版
```bash
# リアルタイムログ
docker-compose logs -f

# 最新100行
docker-compose logs --tail=100
```

### 通常版
コンソールに出力されます

---

## 🔄 アップデート

### Docker版
```bash
# コンテナ停止
docker-compose down

# イメージ再ビルド
docker-compose build --no-cache

# 起動
docker-compose up -d
```

### 通常版
```bash
# サーバーを停止（Ctrl+C）

# コードを更新

# 再起動
python server.py
```

---

## 💡 運用Tips

### 自動起動（Windows）

**タスクスケジューラで設定:**
1. タスクスケジューラを開く
2. 「基本タスクの作成」
3. トリガー: Windowsの起動時
4. 操作: `start_docker.bat` を実行

### 定期バックアップ

**バッチファイル作成:**
```batch
@echo off
cd C:\Users\take_me_hospital\Desktop\N100
copy attendance.db backups\attendance_%date:~0,4%%date:~5,2%%date:~8,2%.db
```

タスクスケジューラで毎日実行

---

## 📞 サポート

問題が解決しない場合：

1. **ログを確認**
2. **Docker/Pythonのバージョン確認**
3. **ファイアウォール設定確認**
4. **ネットワーク設定確認**

---

**セットアップ完了！** 🎉

クライアント側の設定は `SETUP_GUIDE.md` を参照してください。

