"""
Voice Call Interface Component

FLOW:
1. User clicks "Start Voice Call" button
2. Browser requests microphone permission
3. WebSocket connection established to FastAPI backend
4. Audio recorded in 3-second chunks (WebM format)
5. Chunks sent to backend via WebSocket
6. Backend: Deepgram STT → Dual-LLM (Qwen + LLaMA) → Response
7. Response displayed as text + spoken via browser TTS
8. Auto-ends after 30s of silence

COMPONENTS:
- Microphone capture (MediaRecorder API)
- WebSocket streaming
- Audio visualizer
- Silence detection timer
- Browser TTS fallback (window.speechSynthesis)
"""

VOICE_CALL_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Voice Call Interface</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e0e0e0;
            padding: 1rem;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        
        /* Status indicator */
        .status {
            text-align: center;
            padding: 1rem;
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            margin-bottom: 1.5rem;
            font-size: 1.1rem;
            font-weight: 500;
        }
        
        .status-connecting { color: #ffa500; }
        .status-connected { color: #4ade80; }
        .status-processing { color: #60a5fa; }
        .status-error { color: #f87171; }
        
        /* Control buttons */
        .controls {
            display: flex;
            gap: 1rem;
            justify-content: center;
            margin-bottom: 2rem;
        }
        
        .btn {
            padding: 0.875rem 2rem;
            border: none;
            border-radius: 10px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .btn-primary:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(102, 126, 234, 0.4);
        }
        
        .btn-danger {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
        }
        
        .btn-danger:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(245, 87, 108, 0.4);
        }
        
        /* Audio visualizer */
        .audio-visualizer {
            display: none;
            justify-content: center;
            align-items: flex-end;
            gap: 4px;
            height: 60px;
            margin-bottom: 2rem;
        }
        
        .bar {
            width: 6px;
            background: linear-gradient(to top, #667eea, #764ba2);
            border-radius: 3px;
            animation: pulse 1s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0%, 100% { height: 20px; }
            50% { height: 50px; }
        }
        
        /* Conversation transcript */
        .glass-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 1.5rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .glass-card h3 {
            margin-bottom: 1rem;
            color: #a78bfa;
        }
        
        .transcript-box {
            max-height: 400px;
            overflow-y: auto;
            padding: 1rem;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 8px;
        }
        
        .message {
            margin-bottom: 0.75rem;
            padding: 0.75rem;
            border-radius: 8px;
            line-height: 1.5;
        }
        
        .message-user {
            background: rgba(102, 126, 234, 0.2);
            border-left: 3px solid #667eea;
        }
        
        .message-agent {
            background: rgba(74, 222, 128, 0.2);
            border-left: 3px solid #4ade80;
        }
        
        .message-system {
            background: rgba(156, 163, 175, 0.2);
            border-left: 3px solid #9ca3af;
            font-size: 0.9rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <div id="status" class="status status-connecting">Ready to connect</div>
        
        <div class="controls">
            <button id="startBtn" class="btn btn-primary" onclick="startCall()">
                🎤 Start Voice Call
            </button>
            <button id="stopBtn" class="btn btn-danger" onclick="stopCall()" disabled>
                ⏹️ End Call
            </button>
        </div>
        
        <div id="visualizer" class="audio-visualizer" style="display: none;">
            <div class="bar" style="animation-delay: 0s;"></div>
            <div class="bar" style="animation-delay: 0.1s;"></div>
            <div class="bar" style="animation-delay: 0.2s;"></div>
            <div class="bar" style="animation-delay: 0.3s;"></div>
            <div class="bar" style="animation-delay: 0.4s;"></div>
        </div>
        
        <div class="glass-card">
            <h3>💬 Conversation</h3>
            <div id="transcript" class="transcript-box"></div>
        </div>
    </div>
    
    <script>
        // === STATE VARIABLES ===
        let websocket = null;
        let stream = null;
        let isRecording = false;
        let isProcessing = false;  // True when AI is thinking
        let silenceTimer = null;
        let lastSpeechTime = null;
        
        // === CONFIGURATION ===
        const sessionId = "SESSION_ID_PLACEHOLDER";
        const CHUNK_DURATION = 3000;  // Record 3-second audio chunks
        const SILENCE_TIMEOUT = 30000;  // 30 seconds before auto-end
        
        // Agent config (injected by Python)
        const agentConfig = {
            name: typeof AGENT_NAME_PLACEHOLDER !== 'undefined' ? AGENT_NAME_PLACEHOLDER : "Voice Assistant",
            system_prompt: typeof SYSTEM_PROMPT_PLACEHOLDER !== 'undefined' ? SYSTEM_PROMPT_PLACEHOLDER : "You are a helpful AI assistant."
        };
        
        // === UI FUNCTIONS ===
        function setStatus(message, type) {
            const status = document.getElementById('status');
            status.textContent = message;
            status.className = `status status-${type}`;
        }
        
        function addMessage(text, sender) {
            const transcript = document.getElementById('transcript');
            const msg = document.createElement('div');
            msg.className = `message message-${sender}`;
            const label = sender === 'user' ? '👤 You' : sender === 'agent' ? '🤖 Agent' : '⚙️ System';
            msg.innerHTML = `<strong>${label}:</strong> ${text}`;
            transcript.appendChild(msg);
            transcript.scrollTop = transcript.scrollHeight;
        }
        
        // === MAIN CALL FUNCTIONS ===
        async function startCall() {
            try {
                setStatus('🔌 Connecting...', 'connecting');
                
                // Request microphone permission
                stream = await navigator.mediaDevices.getUserMedia({ 
                    audio: {
                        channelCount: 1,
                        sampleRate: 16000,
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true
                    } 
                });
                
                // Connect to backend WebSocket
                websocket = new WebSocket(`ws://localhost:8001/ws/voice/${sessionId}`);
                
                websocket.onopen = () => {
                    setStatus('🟢 Connected - Speak into your microphone', 'connected');
                    
                    // Send agent configuration
                    websocket.send(JSON.stringify({
                        type: 'config',
                        config: agentConfig
                    }));
                    
                    // Update UI
                    document.getElementById('startBtn').disabled = true;
                    document.getElementById('stopBtn').disabled = false;
                    document.getElementById('visualizer').style.display = 'flex';
                    
                    // Start recording
                    isRecording = true;
                    lastSpeechTime = Date.now();
                    startSilenceDetection();
                    recordChunk();
                };
                
                websocket.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    
                    if (data.type === 'connected') {
                        addMessage('Connected to voice server', 'system');
                    } 
                    else if (data.type === 'transcript' && data.is_final) {
                        // User speech transcribed
                        addMessage(data.text, 'user');
                        isProcessing = true;  // Pause silence timer
                        setStatus('🤔 Thinking...', 'processing');
                    } 
                    else if (data.type === 'agent_response') {
                        // AI response received
                        addMessage(data.text, 'agent');
                        lastSpeechTime = Date.now();
                        isProcessing = false;  // Resume silence timer
                        setStatus('🟢 Listening...', 'connected');
                        
                        // Speak response using browser TTS
                        speakText(data.text);
                    } 
                    else if (data.type === 'audio_response') {
                        // Server-side TTS audio (if Cartesia is available)
                        if (data.audio) {
                            playAudio(data.audio);
                        }
                    } 
                    else if (data.type === 'session_timeout') {
                        addMessage(data.message, 'system');
                        setStatus('⏱️ Session ended — silence timeout', 'error');
                        cleanup();
                    } 
                    else if (data.type === 'error') {
                        addMessage(`Error: ${data.message}`, 'system');
                    }
                };
                
                websocket.onerror = (error) => {
                    setStatus('❌ Connection error', 'error');
                };
                
                websocket.onclose = () => {
                    setStatus('Disconnected', 'connecting');
                    cleanup();
                };
                
            } catch (error) {
                setStatus('❌ Microphone access denied', 'error');
                addMessage('Please allow microphone access in your browser settings.', 'system');
            }
        }
        
        function stopCall() {
            if (websocket && websocket.readyState === WebSocket.OPEN) {
                websocket.send(JSON.stringify({ type: 'end_stream' }));
            }
            cleanup();
        }
        
        function cleanup() {
            isRecording = false;
            isProcessing = false;
            stopSilenceDetection();
            lastSpeechTime = null;
            
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
                stream = null;
            }
            
            if (websocket) {
                websocket.close();
                websocket = null;
            }
            
            document.getElementById('startBtn').disabled = false;
            document.getElementById('stopBtn').disabled = true;
            document.getElementById('visualizer').style.display = 'none';
        }
        
        // === AUDIO RECORDING ===
        function recordChunk() {
            if (!isRecording || !stream || !websocket || websocket.readyState !== WebSocket.OPEN) {
                return;
            }
            
            // Determine supported MIME type
            let mimeType = 'audio/webm;codecs=opus';
            if (!MediaRecorder.isTypeSupported(mimeType)) {
                mimeType = 'audio/webm';
            }
            
            const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : {});
            const chunks = [];
            
            recorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    chunks.push(event.data);
                }
            };
            
            recorder.onstop = () => {
                if (chunks.length > 0 && websocket && websocket.readyState === WebSocket.OPEN) {
                    // Combine chunks into WebM blob
                    const blob = new Blob(chunks, { type: recorder.mimeType || 'audio/webm' });
                    
                    // Convert to base64 and send
                    const reader = new FileReader();
                    reader.onloadend = () => {
                        const base64 = reader.result.split(',')[1];
                        if (base64 && base64.length > 100) {
                            websocket.send(JSON.stringify({
                                type: 'audio_chunk',
                                data: base64,
                                timestamp: Date.now()
                            }));
                        }
                    };
                    reader.readAsDataURL(blob);
                }
                
                // Schedule next recording cycle
                if (isRecording) {
                    setTimeout(recordChunk, 100);
                }
            };
            
            // Record for CHUNK_DURATION then stop
            recorder.start();
            setTimeout(() => {
                if (recorder.state === 'recording') {
                    recorder.stop();
                }
            }, CHUNK_DURATION);
        }
        
        // === SILENCE DETECTION ===
        function startSilenceDetection() {
            stopSilenceDetection();
            silenceTimer = setInterval(() => {
                // Don't timeout if AI is processing or not recording
                if (!isRecording || !lastSpeechTime || isProcessing) return;
                
                const elapsed = Date.now() - lastSpeechTime;
                const remaining = Math.max(0, Math.ceil((SILENCE_TIMEOUT - elapsed) / 1000));
                
                if (elapsed >= SILENCE_TIMEOUT) {
                    addMessage(`No speech detected for ${SILENCE_TIMEOUT / 1000} seconds — ending session automatically.`, 'system');
                    setStatus('⏱️ Session ended — silence timeout', 'error');
                    stopCall();
                } else if (remaining <= 3 && remaining > 0) {
                    setStatus(`🟢 Listening... (auto-end in ${remaining}s)`, 'connected');
                }
            }, 1000);
        }
        
        function stopSilenceDetection() {
            if (silenceTimer) {
                clearInterval(silenceTimer);
                silenceTimer = null;
            }
        }
        
        // === AUDIO PLAYBACK ===
        async function playAudio(base64Audio) {
            try {
                // Cancel browser TTS if server audio arrives
                window.speechSynthesis.cancel();
                
                // Decode base64 to audio
                const binaryString = atob(base64Audio);
                const bytes = new Uint8Array(binaryString.length);
                for (let i = 0; i < binaryString.length; i++) {
                    bytes[i] = binaryString.charCodeAt(i);
                }
                
                // Play WAV audio
                const blob = new Blob([bytes.buffer], { type: 'audio/wav' });
                const url = URL.createObjectURL(blob);
                const audio = new Audio(url);
                
                audio.onended = () => URL.revokeObjectURL(url);
                audio.onerror = () => URL.revokeObjectURL(url);
                
                await audio.play();
            } catch (error) {
                console.error('Audio playback error:', error);
            }
        }
        
        // === BROWSER TTS FALLBACK ===
        function speakText(text) {
            if (!text) return;
            
            try {
                window.speechSynthesis.cancel();
                const utterance = new SpeechSynthesisUtterance(text);
                
                // Try to find a good voice
                const voices = window.speechSynthesis.getVoices();
                const preferred = voices.find(v => v.lang === 'en-US' && v.name.includes('Google'));
                if (preferred) utterance.voice = preferred;
                
                utterance.rate = 1.0;
                utterance.pitch = 1.0;
                
                window.speechSynthesis.speak(utterance);
            } catch (error) {
                console.error('Browser TTS error:', error);
            }
        }
        
        // Initialize
        setStatus('Ready to connect', 'connecting');
    </script>
</body>
</html>
"""
