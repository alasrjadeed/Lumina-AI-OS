"""Voice Control API — audio upload, WebSocket streaming, and command execution."""

import asyncio
import json
import time

from fastapi import APIRouter, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from core.log import log
from core.provider import engine
from core.voice import stt, tts, voice_controller

router = APIRouter(prefix="/voice", tags=["Voice Control"])


class SpeakRequest(BaseModel):
    text: str
    voice: str = "shimmer"
    play: bool = True


class TranscribeResponse(BaseModel):
    text: str
    confidence: float = 0.0
    language: str = ""
    provider: str = ""


@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """Upload audio file and get transcription."""
    audio_data = await file.read()
    result = await stt.transcribe(audio_data)
    return {
        "text": result.text,
        "confidence": result.confidence,
        "language": result.language,
        "duration": result.duration_ms,
        "provider": result.provider,
    }


@router.post("/speak")
async def speak_text(req: SpeakRequest):
    """Convert text to speech. Returns audio file path."""
    result = await tts.speak(req.text, voice=req.voice, play=req.play)
    return result


@router.post("/command")
async def voice_command(req: SpeakRequest):
    """Process a voice command end-to-end: STT → Understand → Execute → Reply."""
    result = await voice_controller.process_command(req.text)
    return result


@router.post("/listen")
async def listen_and_execute(file: UploadFile = File(...)):
    """Upload audio, transcribe, understand, execute, reply with TTS audio."""
    audio_data = await file.read()

    # Transcribe
    stt_result = await stt.transcribe(audio_data)
    text = stt_result.text
    if not text:
        return {"status": "no_speech", "text": ""}

    # Process
    cmd_result = await voice_controller.process_command(text)

    # Generate TTS reply audio
    reply = cmd_result.get("reply", "Done.")
    tts_result = await tts.speak(reply, play=False)

    return {
        "status": cmd_result.get("status"),
        "text": text,
        "reply": reply,
        "intent": cmd_result.get("intent"),
        "audio_path": tts_result.path,
    }


@router.websocket("/stream")
async def voice_websocket(websocket: WebSocket):
    """WebSocket for real-time voice streaming.

    Client sends audio chunks (raw PCM), server transcribes and processes.
    """
    await websocket.accept()
    log.info("Voice WebSocket connected")

    audio_buffer = bytearray()

    try:
        while True:
            data = await websocket.receive_bytes()
            audio_buffer.extend(data)

            # Process when we have enough audio (~1 second at 16kHz 16bit)
            if len(audio_buffer) >= 32000:
                stt_result = await stt.transcribe(bytes(audio_buffer))
                text = stt_result.text.strip()
                audio_buffer.clear()

                if text:
                    log.info("Voice WS: transcribed: %s", text[:80])

                    # Process command
                    cmd_result = await voice_controller.process_command(text)
                    reply = cmd_result.get("reply", "Done.")

                    await websocket.send_json({
                        "type": "transcription",
                        "text": text,
                        "confidence": stt_result.confidence,
                    })

                    # Speak reply
                    tts_result = await tts.speak(reply, play=False)
                    with open(tts_result.path, "rb") as f:
                        audio_response = f.read()

                    await websocket.send_json({
                        "type": "reply",
                        "text": reply,
                    })
                    await websocket.send_bytes(audio_response)

    except WebSocketDisconnect:
        log.info("Voice WebSocket disconnected")
    except Exception as e:
        log.error("Voice WebSocket error: %s", e)
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


@router.get("/listen/start")
async def start_listening(wake_word: bool = True):
    """Start continuous voice listening in background."""
    task = asyncio.create_task(
        voice_controller.start_continuous(wake_word_mode=wake_word)
    )
    return {
        "status": "listening",
        "wake_word": wake_word,
        "message": f"Voice control started (wake_word={wake_word})",
    }


@router.post("/listen/stop")
async def stop_listening():
    """Stop continuous voice listening."""
    voice_controller.stop()
    return {"status": "stopped"}


@router.get("/status")
async def voice_status():
    """Get voice system status and available voices."""
    return {
        "listening": voice_controller.listening,
        "recorder_available": voice_controller.recorder.is_available(),
        "stt_providers": voice_controller.stt._providers,
        "tts_voices": tts.list_voices(),
        "conversation_history": voice_controller.get_conversation_history(limit=5),
    }


@router.get("/test")
async def voice_test_page():
    """Simple HTML test page for voice."""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Lumina Voice Test</title>
        <style>
            body { font-family: system-ui; max-width: 600px; margin: 40px auto; padding: 20px; }
            button { padding: 12px 24px; font-size: 16px; margin: 8px; cursor: pointer; }
            #status { margin: 16px 0; padding: 12px; background: #f5f5f5; border-radius: 8px; }
            .recording { background: #ff4444; color: white; }
        </style>
    </head>
    <body>
        <h1>🎤 Lumina Voice Control</h1>
        <div id="status">Ready</div>
        <button onclick="startRecording()">🎤 Record</button>
        <button onclick="toggleListening()">🔴 Continuous Mode</button>
        <button onclick="speakTest()">🔊 Speak Test</button>
        <div id="result" style="margin-top: 20px; white-space: pre-wrap;"></div>
        <script>
            let mediaRecorder = null;
            let audioChunks = [];

            async function startRecording() {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];
                mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
                mediaRecorder.onstop = async () => {
                    const blob = new Blob(audioChunks, { type: 'audio/webm' });
                    const form = new FormData();
                    form.append('file', blob, 'voice.webm');
                    document.getElementById('status').textContent = 'Transcribing...';
                    const r = await fetch('/voice/listen', { method: 'POST', body: form });
                    const data = await r.json();
                    document.getElementById('status').textContent = data.status;
                    document.getElementById('result').textContent =
                        `You: ${data.text}\\n\\nReply: ${data.reply}`;
                };
                mediaRecorder.start();
                document.getElementById('status').textContent = 'Recording...';
                setTimeout(() => mediaRecorder.stop(), 5000);
            }

            let ws = null;
            function toggleListening() {
                if (ws) { ws.close(); ws = null;
                    document.getElementById('status').textContent = 'Disconnected'; return; }
                ws = new WebSocket('ws://' + location.host + '/voice/stream');
                ws.onopen = () => document.getElementById('status').textContent = 'WebSocket connected';
                ws.onmessage = e => {
                    if (typeof e.data === 'string') {
                        const d = JSON.parse(e.data);
                        document.getElementById('result').textContent +=
                            `\\n[${d.type}] ${d.text}`;
                    }
                };
                ws.onclose = () => { ws = null;
                    document.getElementById('status').textContent = 'Disconnected'; };
            }

            async function speakTest() {
                const r = await fetch('/voice/speak', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({text: 'Lumina AI OS voice system is operational.', play: true})
                });
                const d = await r.json();
                document.getElementById('result').textContent = `Spoken: ${d.provider}`;
            }
        </script>
    </body>
    </html>
    """)
