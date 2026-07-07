from __future__ import annotations

import asyncio
import json
import os
import re
import time
from typing import Any

from core.log import log
from core.orchestrator import ceo
from core.provider import engine as ai_engine
from core.voice.echo import EchoDetector
from core.voice.languages import LANGUAGE_VOICES, detect_language, get_voice_for_language, get_wake_word
from core.voice.recorder import AudioRecorder, recorder as _recorder_singleton
from core.voice.stt import STTEngine, stt as _stt_singleton
from core.voice.tts import TTSEngine, tts as _tts_singleton
from core.voice.vad import EnergyVAD


class VoiceController:
    def __init__(
        self,
        recorder: AudioRecorder | None = None,
        stt_engine: STTEngine | None = None,
        tts_engine: TTSEngine | None = None,
        wake_word: str = "lumina",
        confirm_threshold: float = 0.6,
        follow_up_seconds: float = 5.0,
        whisper_min_confidence: float = 0.3,
        whisper_no_speech_threshold: float = 0.5,
    ):
        self.recorder = recorder or _recorder_singleton
        self.stt = stt_engine or _stt_singleton
        self.tts = tts_engine or _tts_singleton
        self.wake_word = wake_word.lower()
        self.confirm_threshold = confirm_threshold
        self.follow_up_seconds = follow_up_seconds
        self.whisper_min_confidence = whisper_min_confidence
        self.whisper_no_speech_threshold = whisper_no_speech_threshold
        self.listening = False
        self._conversation_history: list[dict] = []
        self._echo = EchoDetector()
        self._vad = EnergyVAD()
        self._last_response_time: float = 0.0
        self._in_follow_up: bool = False
        self._reply_in_progress: bool = False
        self._current_language: str = os.getenv("LUMINA_LANGUAGE", "en")
        self._multi_language: bool = True

    # ── Core Voice Loop ──

    async def listen_for_wake_word(self, timeout: float = 30.0) -> str | None:
        log.info("Voice: listening for wake word '%s'...", self.wake_word)

        audio = await self.recorder.record_until_silence(max_duration=timeout)
        if not audio:
            return None

        result = await self.stt.transcribe(audio)
        text = result.text.lower().strip()

        if self._multi_language and result.language:
            self._current_language = result.language[:2]
            log.info("Voice: detected language: %s", self._current_language)

        if self._echo.is_echo(text):
            log.info("Voice: ignored echo: '%s'", text[:50])
            return None

        if not text:
            return None

        wake_word = get_wake_word(self._current_language, self.wake_word)
        if wake_word in text or self.wake_word in text:
            command = self._strip_wake_word(text)
            log.info("Voice: wake word detected. Command: '%s'", command)
            return command or text

        if self._in_follow_up:
            elapsed = time.time() - self._last_response_time
            if elapsed <= self.follow_up_seconds:
                log.info("Voice: follow-up detected: '%s'", text)
                return text

        log.info("Voice: wake word not heard%s",
                 " (in follow-up window)" if self._in_follow_up else "")
        return None

    def _strip_wake_word(self, text: str) -> str:
        command = re.sub(rf"^{re.escape(self.wake_word)}[\s,.:;!]*", "", text, flags=re.IGNORECASE)
        command = re.sub(rf"[\s,.:;!]*{re.escape(self.wake_word)}$", "", command, flags=re.IGNORECASE)
        command = re.sub(rf"[\s,.:;!]*{re.escape(self.wake_word)}[\s,.:;!]*", " ", command, flags=re.IGNORECASE)
        return command.strip()

    async def listen_for_command(self, timeout: float = 10.0) -> str | None:
        audio = await self.recorder.record_until_silence(max_duration=timeout)
        if not audio:
            return None
        result = await self.stt.transcribe(audio)
        text = result.text.strip()

        if self._multi_language and result.language:
            self._current_language = result.language[:2]

        if self._echo.is_echo(text):
            log.info("Voice: ignored echo: '%s'", text[:50])
            return None

        return text or None

    async def process_command(self, text: str) -> dict:
        if not text:
            return {"status": "empty", "reply": ""}

        if self._is_stop_command(text):
            self._reply_in_progress = False
            return {"status": "stopped", "text": text, "reply": ""}

        self._conversation_history.append({"role": "user", "content": text})

        intent = await self._understand_intent(text)

        if intent.get("needs_confirmation", False) and intent.get("confidence", 1.0) < self.confirm_threshold:
                confirmed = await self._confirm_with_user(intent)
                if not confirmed:
                    reply = "Cancelled."
                    if self._multi_language:
                        await self.tts.speak_in_language(reply, lang_code=self._current_language)
                    else:
                        await self.tts.speak(reply)
                self._conversation_history.append({"role": "assistant", "content": reply})
                return {"status": "cancelled", "text": text, "reply": reply}

        plan = await self._plan_task(text, intent)
        result = await self._execute_intent(intent, plan)
        result = await self._tool_result_digest(result)

        reply = await self._generate_reply(text, result)
        self._conversation_history.append({"role": "assistant", "content": reply})

        self._echo.record_utterance(reply)
        self._last_response_time = time.time()
        self._in_follow_up = True

        self._reply_in_progress = True
        if self._multi_language:
            await self.tts.speak_in_language(reply, lang_code=self._current_language)
        else:
            await self.tts.speak(reply)
        self._reply_in_progress = False

        return {
            "status": "completed",
            "text": text,
            "intent": intent,
            "plan": plan,
            "result": result,
            "reply": reply,
        }

    def _is_stop_command(self, text: str) -> bool:
        stop_patterns = [
            r"^(stop|shut up|silence|quiet|enough|halt|cease)",
            r"^(never mind|forget it|nevermind|dont worry)",
            r"^(stop|pause)\s+(speaking|talking|playing)",
        ]
        lower = text.lower().strip()
        for pat in stop_patterns:
            if re.match(pat, lower):
                return True
        return False

    async def _understand_intent(self, text: str) -> dict:
        context = self._get_recent_context()
        prompt = f"""You are the intent parser for a voice-controlled AI assistant named {self.wake_word.title()}.

Current conversation context:
{context}

User command: "{text}"

Analyze the intent. Return ONLY valid JSON:
{{
  "action": "brief action name",
  \"category\": \"chat | code | browser | whatsapp | email | crm | seo | pipeline | system | agent | desktop | memory | voice | vision\",
  "target": "what the command targets (optional)",
  "params": {{"key": "value"}},
  "needs_confirmation": true or false (true if destructive/expensive),
  "confidence": 0.0-1.0,
  "summary": "one-line summary",
  "follow_up": true if this references a previous topic
}}"""
        try:
            resp = await ai_engine.chat([{"role": "user", "content": prompt}])
            text_resp = resp.get("message", {}).get("content", "")
            match = re.search(r"\{.*\}", text_resp, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception as e:
            log.warning("Voice: intent parse failed: %s", e)

        return {
            "action": "chat",
            "category": "chat",
            "params": {"message": text},
            "needs_confirmation": False,
            "confidence": 0.5,
            "summary": text[:80],
        }

    def _get_recent_context(self, limit: int = 6) -> str:
        if not self._conversation_history:
            return "(no prior context)"
        recent = self._conversation_history[-limit:]
        lines = []
        for msg in recent:
            role = msg.get("role", "user")
            content = msg.get("content", "")[:200]
            lines.append(f"{role}: {content}")
        return "\n".join(lines)

    async def _memory_digest(self) -> str:
        """Compress conversation history into a short digest for small models."""
        if len(self._conversation_history) <= 2:
            return self._get_recent_context(limit=4)
        recent = self._conversation_history[-4:]
        lines = []
        for msg in recent:
            lines.append(f"{msg.get('role', 'user')}: {msg.get('content', '')[:150]}")
        raw = "\n".join(lines)
        prompt = f"""Summarize this conversation history in 1-2 short sentences for a voice assistant:

{raw}

Keep only what matters for the next reply. Be concise."""
        try:
            resp = await ai_engine.chat([{"role": "user", "content": prompt}])
            content = resp.get("message", {}).get("content", "")
            if content and len(content) < 300:
                return content
        except Exception:
            pass
        return raw

    async def _tool_result_digest(self, raw_result: dict) -> dict:
        """Compress a large tool result into a concise summary for small models."""
        text = str(raw_result)
        if len(text) < 500:
            return raw_result
        prompt = f"""Condense this tool result into 2-3 key facts:

{text[:2000]}

Return only the essential information as a brief summary."""
        try:
            resp = await ai_engine.chat([{"role": "user", "content": prompt}])
            summary = resp.get("message", {}).get("content", "")
            if summary:
                return {"digest": summary}
        except Exception:
            pass
        return raw_result

    async def _plan_task(self, text: str, intent: dict) -> dict:
        category = intent.get("category", "chat")
        summary = intent.get("summary", text)
        if category == "chat" or not summary:
            return {"steps": [], "strategy": "direct"}

        context_digest = await self._memory_digest()
        prompt = f"""Decompose this voice command into steps if it requires multiple actions.

Conversation context: {context_digest}
Command: "{text}"
Summary: "{summary}"
Category: "{category}"

Return JSON:
{{
  "strategy": "single | parallel | sequential",
  "steps": [
    {{"action": "...", "target": "...", "description": "..."}}
  ]
}}
If single-step, return "strategy": "direct" with empty steps."""
        try:
            resp = await ai_engine.chat([{"role": "user", "content": prompt}])
            text_resp = resp.get("message", {}).get("content", "")
            match = re.search(r"\{.*\}", text_resp, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception:
            pass
        return {"steps": [], "strategy": "direct"}

    async def _confirm_with_user(self, intent: dict) -> bool:
        question = f"Shall I {intent.get('summary', 'proceed')}?"
        log.info("Voice: confirming: %s", question)
        if self._multi_language:
            await self.tts.speak_in_language(question, lang_code=self._current_language)
        else:
            await self.tts.speak(question)

        for _ in range(3):
            response = await self.listen_for_command(timeout=5.0)
            if not response:
                continue
            response_lower = response.lower()
            if any(w in response_lower for w in ["yes", "yeah", "sure", "ok", "go", "do it", "please", "correct"]):
                return True
            if any(w in response_lower for w in ["no", "nope", "nah", "stop", "cancel", "don't", "never mind"]):
                return False
            await self.tts.speak("Please say yes or no.")

        return False

    async def _execute_intent(self, intent: dict, plan: dict | None = None) -> dict:
        category = intent.get("category", "chat")
        params = intent.get("params", {})
        steps = (plan or {}).get("steps", [])

        try:
            if category == "pipeline":
                from core.pipeline import pipeline_builder
                desc = params.get("description", params.get("message", intent.get("summary", "")))
                result = await pipeline_builder.launch(description=desc)
                return result

            elif category == "code":
                from api.code import code_agent
                resp = await code_agent.run(params.get("message", intent.get("summary", "")))
                return {"agent_result": resp.output}

            elif category == "browser":
                from core.browser.agent import browser_agent
                result = await browser_agent.execute(params.get("task", intent.get("summary", "")))
                return result

            elif category == "whatsapp":
                from core.whatsapp.client import whatsapp
                to = params.get("to", "")
                text = params.get("text", params.get("message", ""))
                result = await whatsapp.send_text(to, text)
                return {"sent": str(result)}

            elif category == "email":
                from core.email.client import email_client
                to = params.get("to", "")
                subject = params.get("subject", "")
                body = params.get("body", params.get("message", ""))
                result = await email_client.send(to, subject, body)
                return {"email_sent": str(result)}

            elif category == "desktop":
                from core.desktop.os_automation import DesktopAutomation
                da = DesktopAutomation()
                action = params.get("action", params.get("message", ""))
                result = await da.execute(action)
                return {"desktop": str(result)}

            elif category == "memory":
                from core.memory.engine import MemoryEngine
                me = MemoryEngine()
                result = await me.recall_context(5)
                return {"memory": str(result)[:500]}

            elif category == "vision":
                from core.vision.cortex import VisualCortex
                from core.vision.camera import CameraDevice

                cortex = VisualCortex(
                    camera=CameraDevice(device_id=0),
                    ai_engine=ai_engine,
                    enable_faces=True,
                    enable_description=True,
                )

                if not cortex.is_watching:
                    await cortex.start_watching()

                summary = intent.get("summary", "").lower()

                if "who" in summary or "anyone" in summary or "face" in summary:
                    text = await cortex.describe_current_scene()
                    return {"vision": text, "mode": "describe"}

                elif "look for" in summary or "find" in summary or "search" in summary:
                    target = summary.replace("look for", "").replace("find", "").replace("search for", "").strip()
                    if not target:
                        target = params.get("target", "something")
                    text = await cortex.look_for(target, timeout=15.0)
                    return {"vision": text, "mode": "search"}

                elif "change" in summary or "different" in summary:
                    if cortex.memory.size >= 2:
                        prev = list(cortex.memory.get_all())[-2]
                        curr = cortex.memory.current
                        if prev and curr:
                            prev_s = set(prev.labels)
                            curr_s = set(curr.labels)
                            new_items = curr_s - prev_s
                            gone = prev_s - curr_s
                            parts = []
                            if new_items:
                                parts.append(f"New things: {', '.join(new_items)}")
                            if gone:
                                parts.append(f"Gone: {', '.join(gone)}")
                            text = ". ".join(parts) if parts else "Nothing changed."
                            return {"vision": text, "mode": "change"}
                    text = await cortex.describe_current_scene()
                    return {"vision": text, "mode": "describe"}

                elif "watch" in summary or "keep an eye" in summary or "monitor" in summary:
                    if not cortex.is_watching:
                        await cortex.start_watching()
                    cortex.set_proactive_narration(True)
                    text = "I'm now watching and will tell you if anything changes."
                    return {"vision": text, "mode": "watch"}

                elif "stop" in summary and ("watch" in summary or "look" in summary):
                    await cortex.stop_watching()
                    return {"vision": "I stopped watching.", "mode": "idle"}

                elif "remember" in summary or "seen" in summary:
                    text = cortex.memory.summary(max_observations=5)
                    return {"vision": text, "mode": "memory"}

                elif "ask" in summary or "question" in summary or "what about" in summary:
                    question = summary.replace("ask", "").replace("question", "").replace("what about", "").strip()
                    text = await cortex.ask_about_scene(question or "What's happening?")
                    return {"vision": text, "mode": "qa"}

                else:
                    text = await cortex.what_do_you_see()
                    return {"vision": text, "mode": "describe"}

            elif category == "voice":
                if "stop" in params.get("message", "").lower():
                    self.stop()
                    return {"status": "stopped"}
                return {"status": "voice_command_handled"}

            elif category == "system":
                result = await ceo.orchestrate(intent.get("summary", ""))
                return result.to_dict()

            else:
                result = await ceo.orchestrate(intent.get("summary", ""))
                return result.to_dict()

        except Exception as e:
            log.error("Voice: execution failed: %s", e)
            return {"error": str(e)}

    async def _generate_reply(self, command: str, result: dict) -> str:
        prompt = f"""Generate a brief, natural spoken reply (1-2 sentences) for:

Command: "{command}"
Result: {json.dumps(result, default=str)[:600]}

Reply conversationally. Be concise. Sound like a helpful assistant named {self.wake_word.title()}."""
        try:
            resp = await ai_engine.chat([{"role": "user", "content": prompt}])
            return resp.get("message", {}).get("content", "Done.")
        except Exception:
            return "Done."

    # ── Continuous Listening Loop ──

    async def start_continuous(self, wake_word_mode: bool = True) -> None:
        self.listening = True
        log.info("Voice: continuous mode started (wake_word=%s)", wake_word_mode)
        self._echo.clear()

        ready_msg = "Lumina AI OS voice control is ready."
        if self._multi_language:
            await self.tts.speak_in_language(ready_msg, lang_code=self._current_language)
        else:
            await self.tts.speak(ready_msg)

        while self.listening:
            try:
                timeout = 60.0
                if wake_word_mode:
                    command = await self.listen_for_wake_word(timeout=timeout)
                else:
                    command = await self.listen_for_command(timeout=timeout)

                if not command:
                    continue

                result = await self.process_command(command)

                if result.get("status") == "stopped":
                    log.info("Voice: stopped by user command")
                    if self._multi_language:
                        await self.tts.speak_in_language("Stopped.", lang_code=self._current_language)
                    else:
                        await self.tts.speak("Stopped.")
                    continue

                reply = result.get("reply", "")
                if reply:
                    log.info("Voice: command='%s' -> reply='%s'",
                             command[:60], reply[:60])

            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error("Voice: loop error: %s", e)
                try:
                    err_msg = f"Sorry, I encountered an error: {str(e)[:100]}"
                    if self._multi_language:
                        await self.tts.speak_in_language(err_msg, lang_code=self._current_language)
                    else:
                        await self.tts.speak(err_msg)
                except Exception:
                    pass

        self.listening = False
        self._in_follow_up = False
        log.info("Voice: continuous mode stopped")

    def stop(self) -> None:
        self.listening = False
        self._in_follow_up = False
        self._reply_in_progress = False

    def set_language(self, lang_code: str) -> None:
        if lang_code in LANGUAGE_VOICES or lang_code[:2] in LANGUAGE_VOICES:
            self._current_language = lang_code[:2]
            lv = get_voice_for_language(self._current_language)
            log.info("Voice: language set to %s (%s)", lv.name, self._current_language)

    def get_language(self) -> str:
        return self._current_language

    def list_languages(self) -> list[dict]:
        from core.voice.languages import list_supported_languages
        return list_supported_languages()

    def get_conversation_history(self, limit: int = 10) -> list[dict]:
        return self._conversation_history[-limit:]

    def clear_conversation(self) -> None:
        self._conversation_history.clear()
        self._echo.clear()
        self._in_follow_up = False


voice_controller = VoiceController()
