#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI 版提醒助手
- 后端负责计时、触发提醒（打开 URL + 播放音效）
- 前端纯 Web（静态 HTML/JS/CSS），通过 API 控制与轮询状态
- 历史持久化：history.json；配置：config.json
"""

import json
import os
import threading
import time
import webbrowser
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, validator
from openai import OpenAI

# 音效支持
try:
    import pygame

    SOUND_AVAILABLE = True
except Exception:
    SOUND_AVAILABLE = False

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "web"
DEFAULT_INDEX = STATIC_DIR / "index.html"
OPENROUTER_KEY_FILE = BASE_DIR / "openrouter.key"
DEFAULT_PORT = int(os.getenv("APP_PORT", "8765"))

DEFAULTS = {
    "url": "https://www.notion.so/",
    "total_min": 60,
    "first_min": 5,
    "second_min": 10,
    "subseq_min": 15,
    "chrome_path": "",
    "sound_enabled": True,
    "sound_file": "default_reminder.mp3",
}


class ReminderConfig(BaseModel):
    url: str = Field(..., min_length=5)
    total_min: int = Field(..., gt=0)
    first_min: int = Field(..., gt=0)
    second_min: int = Field(..., gt=0)
    subseq_min: int = Field(..., gt=0)
    chrome_path: str = ""
    sound_enabled: bool = True
    sound_file: str = ""
    expectation: str = ""

    @validator("url")
    def validate_url(cls, v):
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("URL 必须以 http:// 或 https:// 开头")
        return v


class NotePayload(BaseModel):
    note: str = Field("", max_length=2000)
    timestamp: Optional[str] = None


class ChatPayload(BaseModel):
    messages: List[Dict[str, str]]
    timeframe: str = "day"  # day/week/month
    prompt_type: str = "summary"  # summary/reflection/advice
    model: str = "openai/gpt-5-mini"


class LLMManager:
    def __init__(self):
        self.client: Optional[OpenAI] = None
        self.model = "openai/gpt-5-mini"
        self._last_key: Optional[str] = None
        self._init_client(force=True)

    def _read_key(self) -> Optional[str]:
        key = os.getenv("OPENROUTER_API_KEY")
        if not key and OPENROUTER_KEY_FILE.exists():
            lines = OPENROUTER_KEY_FILE.read_text().splitlines()
            for line in lines:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                key = line
                break
        return key or None

    def _init_client(self, force=False):
        key = self._read_key()
        if not key:
            self.client = None
            self._last_key = None
            return
        if force or key != self._last_key:
            try:
                self.client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=key)
                self._last_key = key
            except Exception:
                self.client = None
                self._last_key = None

    def _get_client(self) -> OpenAI:
        if not self.client:
            self._init_client(force=True)
        if not self.client:
            raise RuntimeError("缺少 OpenRouter API Key")
        return self.client

    def encourage(self, history_records):
        client = self._get_client()
        recent = history_records[-5:]
        summary_lines = []
        for r in recent:
            ts = r.get("timestamp")
            note = r.get("note") or ""
            exp = r.get("expectation") or ""
            status = r.get("status")
            summary_lines.append(f"- [{ts}] 状态:{status} 预期:{exp} 备注:{note}")
        prompt = (
            "你是一个友好的提醒助手，请基于最近的提醒记录，给用户一句鼓励或打气，保持中文简短积极。"
            "\n最近记录：\n" + "\n".join(summary_lines)
        )
        try:
            completion = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个简短积极的鼓励助手。"},
                    {"role": "user", "content": prompt},
                ],
            )
            return completion.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"调用 LLM 失败: {e}")

    def chat(self, payload: ChatPayload, context: str):
        client = self._get_client()
        base = {
            "summary": "请结合提供的上下文，总结用户的进展，并给出一句鼓励，保持简短。",
            "reflection": "请结合提供的上下文，帮助用户进行反思：哪些做得好，哪些可改进，用中文简短列出。",
            "advice": "请结合提供的上下文，给出下一步建议，列出 2-3 条中文要点，简短。",
        }
        system_prompt = base.get(payload.prompt_type, base["summary"])
        context_text = f"上下文（最近记录）：\n{context}"
        # 拼出发送给模型的消息列表
        assembled = [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": context_text},
        ] + payload.messages
        # 便于前端显示的完整 prompt 文本
        prompt_view = "\n\n".join([f"{m['role']}: {m['content']}" for m in assembled])
        try:
            completion = client.chat.completions.create(
                model=payload.model or self.model,
                messages=assembled,
            )
            usage = getattr(completion, "usage", None)
            return {
                "message": completion.choices[0].message.content,
                "usage": usage.model_dump() if usage else None,
                "prompt": prompt_view,
            }
        except Exception as e:
            raise RuntimeError(f"调用 LLM 失败: {e}")


class SoundManager:
    def __init__(self):
        self.enabled = SOUND_AVAILABLE
        self.initialized = False
        if self.enabled:
            try:
                pygame.mixer.init()
                self.initialized = True
            except Exception:
                self.enabled = False

    def play(self, sound_file=None):
        if not self.enabled or not self.initialized:
            return
        try:
            if sound_file and os.path.exists(sound_file):
                pygame.mixer.music.load(sound_file)
                pygame.mixer.music.play()
            elif os.path.exists("default_reminder.mp3"):
                pygame.mixer.music.load("default_reminder.mp3")
                pygame.mixer.music.play()
        except Exception:
            pass


class ConfigManager:
    def __init__(self):
        self.config_file = BASE_DIR / "config.json"

    def load(self):
        try:
            if self.config_file.exists():
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                result = DEFAULTS.copy()
                result.update(data)
                return result
        except Exception:
            pass
        return DEFAULTS.copy()

    def save(self, cfg: dict):
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
        except Exception:
            pass


class HistoryManager:
    def __init__(self, max_records=500):
        self.history_file = BASE_DIR / "history.json"
        self.max_records = max_records
        self.records = []
        self.load()

    def load(self):
        try:
            if self.history_file.exists():
                with open(self.history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    self.records = data[-self.max_records :]
        except Exception:
            self.records = []
        return self.records

    def add(self, record):
        self.records.append(record)
        if len(self.records) > self.max_records:
            self.records = self.records[-self.max_records :]
        self._persist()
        return self.records

    def update_last_note(self, note: str):
        if not self.records:
            return
        self.records[-1]["note"] = note
        self._persist()
        return self.records[-1]

    def update_note_by_timestamp(self, timestamp: str, note: str):
        for r in reversed(self.records):
            if r.get("timestamp") == timestamp:
                r["note"] = note
                self._persist()
                return r
        return None

    def clear(self):
        self.records = []
        self._persist()

    def enrich_missing_intervals(self):
        """为缺少 expected/actual 的历史补充字段，必要时持久化"""
        changed = False
        prev_dt = None
        for r in self.records:
            ts = r.get("timestamp")
            try:
                dt = datetime.fromisoformat(ts) if ts else None
            except Exception:
                dt = None
            if "expected_sec" not in r or r.get("expected_sec") is None:
                # 缺失预期时，给一个默认 10 分钟，避免前端空白
                r["expected_sec"] = 10 * 60
                changed = True
            if prev_dt and (r.get("actual_sec") is None or r.get("actual_sec") == ""):
                r["actual_sec"] = int((dt - prev_dt).total_seconds()) if dt else None
                changed = True
            prev_dt = dt or prev_dt
        if changed:
            self._persist()
        return self.records

    def _persist(self):
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.records, f, ensure_ascii=False, indent=2)
        except Exception:
            pass


class ReminderEngine:
    """管理计时与提醒触发"""

    def __init__(self, history: HistoryManager, sound: SoundManager):
        self.history = history
        self.sound = sound
        self.lock = threading.Lock()
        self.running = False
        self.elapsed = 0
        self.count = 0
        self.total_sec = 0
        self.intervals: List[int] = []
        self.subseq_sec = 0
        self.url = ""
        self.browser = None
        self.chrome_path = ""
        self.sound_enabled = True
        self.sound_file = ""
        self.seconds_until_next = 0
        self.pending_wait = 0
        self.status_msg = "待机中"
        self.stop_event = threading.Event()
        self.worker: Optional[threading.Thread] = None
        self.last_expected = None
        self.current_expectation = ""

    def start(self, cfg: ReminderConfig):
        with self.lock:
            if self.running:
                raise RuntimeError("已在运行中")
            self.running = True
            self.elapsed = 0
            self.count = 0
            self.total_sec = cfg.total_min * 60
            self.intervals = [cfg.first_min * 60, cfg.second_min * 60]
            self.subseq_sec = cfg.subseq_min * 60
            self.url = cfg.url
            self.chrome_path = cfg.chrome_path.strip()
            self.sound_enabled = cfg.sound_enabled
            self.sound_file = cfg.sound_file.strip()
            self.current_expectation = cfg.expectation.strip()
            self.stop_event.clear()
            self.status_msg = "运行中"
            # 浏览器实例
            self.browser = None
            if self.chrome_path:
                try:
                    self.browser = webbrowser.get(self.chrome_path)
                except Exception:
                    self.browser = None
            self.last_expected = None

            # 启动线程
            self.worker = threading.Thread(target=self._run_loop, daemon=True)
            self.worker.start()

    def stop(self):
        with self.lock:
            if not self.running:
                return
            self.running = False
            self.stop_event.set()
            self.status_msg = "已停止"

    def _run_loop(self):
        # 立即触发一次
        self._open_now()
        self._schedule_next()
        while self.running and not self.stop_event.is_set():
            if self.seconds_until_next > 0:
                time.sleep(1)
                self.seconds_until_next -= 1
                self._update_progress()
            else:
                self.elapsed += self.pending_wait
                self._open_now()
                self._schedule_next()

    def _open_now(self):
        self.count += 1
        success = True
        try:
            if self.browser:
                self.browser.open(self.url)
            else:
                webbrowser.open(self.url)
            if self.sound_enabled:
                sf = self.sound_file or None
                threading.Thread(target=lambda: self.sound.play(sf), daemon=True).start()
            self.status_msg = f"第 {self.count} 次提醒已触发"
        except Exception as e:
            success = False
            self.status_msg = f"打开失败: {e}"
        finally:
            self._record_history(success)

    def _schedule_next(self):
        if self.count <= len(self.intervals):
            wait = self.intervals[self.count - 1]
        else:
            wait = self.subseq_sec

        if self.elapsed + wait >= self.total_sec:
            self.seconds_until_next = 0
            self.pending_wait = 0
            self.status_msg = "完成"
            self.stop()
            return

        self.pending_wait = wait
        self.last_expected = wait
        self.seconds_until_next = wait
        self._update_progress()

    def _update_progress(self):
        pass  # 状态由 status() 计算

    def status(self):
        with self.lock:
            return {
                "running": self.running,
                "status": self.status_msg,
                "count": self.count,
                "elapsed": self.elapsed,
                "total": self.total_sec,
                "next_in": self.seconds_until_next,
                "pending_wait": self.pending_wait,
                "progress": int(
                    ((self.pending_wait - self.seconds_until_next) / self.pending_wait) * 100
                )
                if self.pending_wait
                else 0,
            }

    def _record_history(self, success=True):
        now = datetime.now()
        actual_sec = None
        if self.history.records:
            prev = self.history.records[-1].get("timestamp")
            try:
                prev_dt = datetime.fromisoformat(prev)
                actual_sec = int((now - prev_dt).total_seconds())
            except Exception:
                actual_sec = None

        entry = {
            "timestamp": now.isoformat(timespec="seconds"),
            "count": self.count,
            "url": self.url,
            "status": "success" if success else "failed",
            "note": "",
            "expected_sec": self.last_expected if self.last_expected else None,
            "actual_sec": actual_sec,
            "expectation": self.current_expectation,
        }
        self.history.add(entry)


# 初始化核心组件
config_mgr = ConfigManager()
history_mgr = HistoryManager()
sound_mgr = SoundManager()
engine = ReminderEngine(history_mgr, sound_mgr)
llm_mgr = LLMManager()

app = FastAPI(title="Reminder Web")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def ensure_static():
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    if not DEFAULT_INDEX.exists():
        DEFAULT_INDEX.write_text("<h1>Reminder Web</h1>", encoding="utf-8")


@app.get("/api/config")
def get_config():
    return config_mgr.load()


@app.post("/api/config")
def save_config(cfg: ReminderConfig):
    data = cfg.dict()
    config_mgr.save(data)
    return {"ok": True}


@app.post("/api/start")
def start(cfg: ReminderConfig):
    try:
        engine.start(cfg)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/stop")
def stop():
    engine.stop()
    return {"ok": True}


@app.get("/api/status")
def status():
    return engine.status()


@app.get("/api/history")
def history():
    records = history_mgr.enrich_missing_intervals()
    return {"records": records[-200:]}


@app.post("/api/history/clear")
def clear_history():
    history_mgr.clear()
    return {"ok": True}


@app.post("/api/history/note")
def add_note(payload: NotePayload):
    note = payload.note.strip()
    if payload.timestamp:
        updated = history_mgr.update_note_by_timestamp(payload.timestamp, note)
        if not updated:
            raise HTTPException(status_code=404, detail="未找到该时间戳的记录")
        return {"ok": True, "record": updated}
    # 默认更新最新一条
    if not history_mgr.records:
        raise HTTPException(status_code=400, detail="暂无提醒记录可添加备注")
    updated = history_mgr.update_last_note(note)
    return {"ok": True, "record": updated}


def _context_by_timeframe(records, timeframe: str):
    today = datetime.now().date()
    if timeframe == "day":
        days = 0
    elif timeframe == "week":
        days = 6
    else:
        days = 29
    start = today - timedelta(days=days)
    filtered = []
    for r in records:
        try:
            dt = datetime.fromisoformat(r.get("timestamp"))
        except Exception:
            continue
        if dt.date() >= start:
            filtered.append(r)
    lines = []
    for r in filtered[-50:]:
        lines.append(
            f"[{r.get('timestamp')}] 状态:{r.get('status')} 预期:{r.get('expectation','')} 备注:{r.get('note','')}"
        )
    return "\n".join(lines) or "暂无上下文"


@app.post("/api/llm/chat")
def llm_chat(payload: ChatPayload):
    try:
        context = _context_by_timeframe(history_mgr.records, payload.timeframe)
        result = llm_mgr.chat(payload, context)
        return {"ok": True, **result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/llm/encourage")
def llm_encourage():
    try:
        message = llm_mgr.encourage(history_mgr.records)
        return {"ok": True, "message": message}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/")
def index():
    return FileResponse(DEFAULT_INDEX)

@app.get("/chat.html")
def chat_page():
    chat_file = STATIC_DIR / "chat.html"
    if chat_file.exists():
        return FileResponse(chat_file)
    raise HTTPException(status_code=404, detail="chat.html not found")


app.mount("/web", StaticFiles(directory=STATIC_DIR), name="web")


def main():
    import uvicorn

    uvicorn.run(
        "web_reminder:app",
        host="0.0.0.0",
        port=DEFAULT_PORT,
        reload=False,
    )


if __name__ == "__main__":
    main()
