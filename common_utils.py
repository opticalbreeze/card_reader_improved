#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
共通ユーティリティ関数

このモジュールには、複数のファイルで使用される共通関数が定義されています。
重複を避けるため、すべての共通処理はここに集約されています。

主要な関数:
    - get_mac_address(): MACアドレス取得
    - load_config(): 設定ファイル読み込み
    - save_config(): 設定ファイル保存
    - check_server_connection(): サーバー接続チェック
    - send_attendance_to_server(): サーバーへのデータ送信
    - get_pcsc_commands(): PC/SCコマンド取得
    - is_valid_card_id(): カードID検証
    - is_duplicate_attendance(): 重複打刻チェック
    - setup_windows_encoding(): Windows用エンコーディング設定

使用例:
    from common_utils import get_mac_address, load_config
    
    terminal_id = get_mac_address()
    config = load_config()
"""

import uuid
import json
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
import requests

from constants import (
    DEFAULT_SERVER_URL,
    CONFIG_FILE,
    TIMEOUT_HEALTH_CHECK,
    TIMEOUT_SERVER_REQUEST,
    API_HEALTH,
    API_ATTENDANCE
)


# ============================================================================
# システム情報取得
# ============================================================================

def get_mac_address() -> str:
    """
    端末のMACアドレスを取得
    
    Returns:
        str: MACアドレス（例: "AA:BB:CC:DD:EE:FF"）
    """
    mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
    return ":".join([mac[i:i+2] for i in range(0, 12, 2)]).upper()


# ============================================================================
# 設定ファイル管理
# ============================================================================

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    設定ファイルを読み込む
    
    Args:
        config_path: 設定ファイルのパス（Noneの場合はデフォルト）
    
    Returns:
        dict: 設定辞書
    """
    if config_path is None:
        config_path = CONFIG_FILE
    
    from constants import (
        DEFAULT_RETRY_INTERVAL,
        LCD_I2C_ADDR_DEFAULT,
        LCD_I2C_BUS_DEFAULT
    )
    
    default_config = {
        "server_url": DEFAULT_SERVER_URL,
        "retry_interval": DEFAULT_RETRY_INTERVAL,
        "lcd_settings": {
            "i2c_addr": LCD_I2C_ADDR_DEFAULT,
            "i2c_bus": LCD_I2C_BUS_DEFAULT,
            "backlight": True
        },
        "beep_settings": {
            "enabled": True,
            "card_read": False,
            "success": True,
            "fail": True
        }
    }
    
    config_file_path = Path(config_path)
    
    if not config_file_path.exists():
        return default_config
    
    try:
        with open(config_file_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # デフォルト設定をマージ（設定ファイルにない項目はデフォルト値を使用）
        merged_config = default_config.copy()
        merged_config.update(config)
        
        # ネストされた辞書もマージ
        if 'lcd_settings' in config:
            merged_config['lcd_settings'] = {
                **default_config['lcd_settings'],
                **config['lcd_settings']
            }
        
        if 'beep_settings' in config:
            merged_config['beep_settings'] = {
                **default_config['beep_settings'],
                **config['beep_settings']
            }
        
        return merged_config
    except Exception as e:
        print(f"[警告] 設定ファイル読み込みエラー: {e}")
        print("[情報] デフォルト設定を使用します")
        return default_config


def save_config(config: Dict[str, Any], config_path: Optional[str] = None) -> bool:
    """
    設定ファイルを保存
    
    Args:
        config: 設定辞書
        config_path: 設定ファイルのパス（Noneの場合はデフォルト）
    
    Returns:
        bool: 保存成功したかどうか
    """
    if config_path is None:
        config_path = CONFIG_FILE
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[エラー] 設定ファイル保存エラー: {e}")
        return False


# ============================================================================
# サーバー通信
# ============================================================================

def check_server_connection(server_url: Optional[str] = None) -> bool:
    """
    サーバー接続をチェック
    
    Args:
        server_url: サーバーURL（Noneの場合は設定ファイルから読み込み）
    
    Returns:
        bool: サーバーが利用可能かどうか
    """
    if server_url is None:
        config = load_config()
        server_url = config.get('server_url')
    
    if not server_url:
        return False
    
    try:
        response = requests.get(
            f"{server_url}{API_HEALTH}",
            timeout=TIMEOUT_HEALTH_CHECK
        )
        return response.status_code == 200
    except Exception:
        return False


def send_attendance_to_server(
    idm: str,
    timestamp: str,
    terminal_id: str,
    server_url: Optional[str] = None
) -> tuple[bool, Optional[str]]:
    """
    サーバーに打刻データを送信
    
    Args:
        idm: カードID
        timestamp: タイムスタンプ（ISO8601形式）
        terminal_id: 端末ID
        server_url: サーバーURL（Noneの場合は設定ファイルから読み込み）
    
    Returns:
        tuple: (成功したかどうか, エラーメッセージまたはNone)
    """
    if server_url is None:
        config = load_config()
        server_url = config.get('server_url')
    
    if not server_url:
        return False, "サーバーURLが設定されていません"
    
    data = {
        'idm': idm,
        'timestamp': timestamp,
        'terminal_id': terminal_id
    }
    
    try:
        response = requests.post(
            f"{server_url}{API_ATTENDANCE}",
            json=data,
            timeout=TIMEOUT_SERVER_REQUEST
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success':
                return True, None
            
            # 重複データの場合は成功として扱う
            message = result.get('message', '').lower()
            if any(keyword in message for keyword in ['重複', 'duplicate', '既に']):
                return True, None
            
            return False, result.get('message', 'サーバーエラー')
        
        return False, f"HTTP {response.status_code}"
    
    except requests.exceptions.ConnectionError:
        return False, "サーバー接続エラー"
    except requests.exceptions.Timeout:
        return False, "タイムアウト"
    except Exception as e:
        return False, f"予期しないエラー: {e}"


# ============================================================================
# エンコーディング設定（Windows用）
# ============================================================================

def setup_windows_encoding():
    """
    Windows環境での文字化け対策: UTF-8出力を強制
    """
    if sys.platform != 'win32':
        return
    
    # 標準出力・標準エラー出力のエンコーディングをUTF-8に設定
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')
    
    # コンソールのコードページをUTF-8に設定
    try:
        os.system('chcp 65001 >nul 2>&1')
    except Exception:
        pass
    
    # 環境変数でUTF-8を強制
    os.environ['PYTHONIOENCODING'] = 'utf-8'


# ============================================================================
# PC/SCコマンド取得
# ============================================================================

def get_pcsc_commands(reader_name: str) -> list:
    """
    リーダー名に応じてPC/SCコマンドセットを返す
    
    Args:
        reader_name: リーダー名
    
    Returns:
        list: APDUコマンドのリスト
    """
    from constants import (
        PCSC_CMD_UID_VARIABLE,
        PCSC_CMD_UID_4BYTE,
        PCSC_CMD_UID_7BYTE,
        PCSC_CMD_UID_10BYTE,
        PCSC_CMD_GET_DATA,
        PCSC_CMD_FELICA_IDM
    )
    
    name = str(reader_name).upper()
    
    # Sony/PaSoRi 系（FeliCa対応）
    if any(k in name for k in ["SONY", "RC-S", "PASORI"]):
        return [
            PCSC_CMD_UID_VARIABLE,
            PCSC_CMD_UID_4BYTE,
            PCSC_CMD_UID_7BYTE,
            PCSC_CMD_FELICA_IDM,
            PCSC_CMD_GET_DATA,
        ]
    
    # Circle CIR315 系
    if any(k in name for k in ["CIRCLE", "CIR315", "CIR-315"]):
        return [
            PCSC_CMD_UID_VARIABLE,
            PCSC_CMD_UID_4BYTE,
            PCSC_CMD_GET_DATA,
            PCSC_CMD_FELICA_IDM,
            PCSC_CMD_UID_7BYTE,
        ]
    
    # 汎用リーダー
    return [
        PCSC_CMD_UID_VARIABLE,
        PCSC_CMD_UID_4BYTE,
        PCSC_CMD_UID_7BYTE,
        PCSC_CMD_UID_10BYTE,
        PCSC_CMD_GET_DATA,
    ]


# ============================================================================
# カードID検証
# ============================================================================

def is_valid_card_id(card_id: str) -> bool:
    """
    カードIDが有効かどうかをチェック

    Args:
        card_id: カードID

    Returns:
        bool: 有効なカードIDかどうか
    """
    from constants import INVALID_CARD_IDS

    if not card_id or len(card_id) < 8:
        return False

    return card_id.upper() not in [id.upper() for id in INVALID_CARD_IDS]


# ============================================================================
# チャタリング防止（同一時刻打刻チェック）
# ============================================================================

def is_duplicate_attendance(card_id: str, timestamp: str, history: dict) -> tuple:
    """
    同じカードIDで同じ日付・時刻（分単位）の打刻が既にあるかチェック
    
    Args:
        card_id: カードID
        timestamp: タイムスタンプ（ISO8601形式）
        history: 履歴辞書 {card_id: {'timestamp': str, 'datetime': datetime}}
    
    Returns:
        tuple: (is_duplicate: bool, message: str)
    """
    from datetime import datetime
    from constants import ENABLE_SAME_MINUTE_CHECK, SAME_MINUTE_THRESHOLD
    
    if not ENABLE_SAME_MINUTE_CHECK:
        return False, ""
    
    try:
        current_dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        current_minute_key = current_dt.strftime("%Y-%m-%d %H:%M")
        
        if card_id in history:
            last_record = history[card_id]
            last_dt = last_record.get('datetime')
            
            if last_dt:
                last_minute_key = last_dt.strftime("%Y-%m-%d %H:%M")
                
                # 同じ分（YYYY-MM-DD HH:MM）であれば重複
                if current_minute_key == last_minute_key:
                    time_diff = (current_dt - last_dt).total_seconds()
                    
                    if time_diff < SAME_MINUTE_THRESHOLD:
                        return True, f"同一時刻打刻済み ({last_minute_key})"
        
        # 履歴を更新
        history[card_id] = {
            'timestamp': timestamp,
            'datetime': current_dt
        }
        
        return False, ""
    
    except Exception as e:
        # エラーが発生した場合は重複チェックをスキップ
        print(f"[警告] 重複チェックエラー: {e}")
        return False, ""