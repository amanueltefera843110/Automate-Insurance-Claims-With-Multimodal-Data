"""FastAPI service for context-aware voice answers without exposing transcripts.

This service keeps user-provided context snippets and recent conversation
transcripts in memory so that responses can reference both uploaded documents
and what speakers just said. Only the final model answer is returned; the raw
transcript stays internal to keep latency and bandwidth low.
"""

import os
import tempfile
from typing import List

from fastapi import FastAPI, HTTPException, UploadFile
from openai import OpenAI

# Initialize OpenAI client once
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI(title="Voice Assistant", description="Answer using uploaded context and live audio")

# In-memory storage for uploaded context and recent transcripts
_CONTEXT_MEMORY: List[str] = []
_CONVERSATION_TRANSCRIPTS: List[str] = []
_MAX_TRANSCRIPT_HISTORY = 5  # Keep only the last few turns to avoid slow, long prompts


def _transcribe_audio(path: str) -> str:
    """Transcribe an audio file using the Whisper API."""
    with open(path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text",
        )
    return transcription


def _build_prompt(transcript: str) -> str:
    """Construct the user prompt from context and recent conversation."""
    # Keep short rolling history to avoid lag
    _CONVERSATION_TRANSCRIPTS.append(transcript)
    del _CONVERSATION_TRANSCRIPTS[:-_MAX_TRANSCRIPT_HISTORY]

    context_blob = "\n".join(_CONTEXT_MEMORY).strip() or "(no additional context provided)"
    conversation_blob = "\n".join(_CONVERSATION_TRANSCRIPTS)

    return (
        "You are assisting in a live conversation. Use the uploaded context to"
        " ground your answers, but reply concisely and directly to the latest"
        " question.\n\n"
        f"Context information:\n{context_blob}\n\n"
        f"Recent conversation transcripts:\n{conversation_blob}"
    )


@app.post("/upload_context")
async def upload_context(file: UploadFile):
    """Upload a text file with background knowledge for future answers."""
    text = (await file.read()).decode("utf-8", errors="ignore").strip()
    if text:
        _CONTEXT_MEMORY.append(text)
    return {"status": "uploaded", "context_items": len(_CONTEXT_MEMORY)}


@app.post("/process_audio")
async def process_audio(file: UploadFile):
    """Transcribe audio and return an answer based on context and conversation."""
    if client.api_key is None:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured")

    # Persist upload to a temporary file for Whisper
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
        temp_audio.write(await file.read())
        temp_path = temp_audio.name

    try:
        transcript = _transcribe_audio(temp_path)
    finally:
        # Clean up the temporary file to avoid disk bloat
        try:
            os.remove(temp_path)
        except OSError:
            pass

    prompt = _build_prompt(transcript)

    chat_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You analyze live audio and provide helpful answers instantly.",
            },
            {"role": "user", "content": prompt},
        ],
    )

    answer = chat_response.choices[0].message.content
    return {"answer": answer}


@app.post("/reset_context")
async def reset_context():
    """Clear stored context and transcripts."""
    _CONTEXT_MEMORY.clear()
    _CONVERSATION_TRANSCRIPTS.clear()
    return {"status": "reset"}
