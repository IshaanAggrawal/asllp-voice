import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useVoiceStream } from '../../hooks/useVoiceStream';
import { sessionsAPI } from '../../lib/api';

export default function VoiceCall() {
    const router = useRouter();
    const { session_id } = router.query;
    const [inputText, setInputText] = useState('');

    const {
        isConnected,
        messages,
        transcript,
        error,
        sendTextMessage,
        endStream,
    } = useVoiceStream(session_id as string);

    const handleSendText = () => {
        if (inputText.trim()) {
            sendTextMessage(inputText);
            setInputText('');
        }
    };

    const handleEndCall = async () => {
        if (session_id) {
            await sessionsAPI.end(session_id as string);
        }
        endStream();
        router.push('/');
    };

    return (
        <div className="container">
            <div className="call-interface">
                <div className="call-header">
                    <h1>Voice Call Session</h1>
                    <div className="status">
                        <span className={`status-dot ${isConnected ? 'connected' : 'disconnected'}`}></span>
                        {isConnected ? 'Connected' : 'Disconnected'}
                    </div>
                </div>

                {error && <div className="error">{error}</div>}

                <div className="messages-container">
                    {messages.map((msg, idx) => (
                        <div key={idx} className={`message message-${msg.type}`}>
                            <span className="message-type">{msg.type}</span>
                            <div className="message-content">
                                {msg.text || msg.message || JSON.stringify(msg)}
                            </div>
                            {msg.timestamp && (
                                <small className="timestamp">
                                    {new Date(msg.timestamp).toLocaleTimeString()}
                                </small>
                            )}
                        </div>
                    ))}
                </div>

                <div className="input-area">
                    <input
                        type="text"
                        value={inputText}
                        onChange={(e) => setInputText(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleSendText()}
                        placeholder="Type your message (for testing without audio)..."
                        disabled={!isConnected}
                    />
                    <button
                        onClick={handleSendText}
                        disabled={!isConnected || !inputText.trim()}
                        className="btn btn-primary"
                    >
                        Send
                    </button>
                </div>

                <div className="call-controls">
                    <button onClick={handleEndCall} className="btn btn-danger">
                        End Call
                    </button>
                </div>

                <div className="info-box">
                    <p><strong>Note:</strong> This is a text-based interface for testing. Audio integration requires:</p>
                    <ul>
                        <li>Microphone access implementation</li>
                        <li>Audio recording and chunking</li>
                        <li>STT integration (Deepgram or local Whisper)</li>
                        <li>TTS integration (Cartesia or local TTS)</li>
                    </ul>
                </div>
            </div>

            <style jsx>{`
        .container {
          max-width: 900px;
          margin: 0 auto;
          padding: 40px 20px;
        }

        .call-interface {
          background: white;
          border-radius: 12px;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
          overflow: hidden;
        }

        .call-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 24px;
          border-bottom: 1px solid #e5e7eb;
        }

        h1 {
          font-size: 24px;
          font-weight: 700;
          color: #111827;
          margin: 0;
        }

        .status {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 14px;
          color: #6b7280;
        }

        .status-dot {
          width: 10px;
          height: 10px;
          border-radius: 50%;
        }

        .status-dot.connected {
          background: #10b981;
        }

        .status-dot.disconnected {
          background: #ef4444;
        }

        .error {
          background: #fee2e2;
          color: #dc2626;
          padding: 12px 24px;
          margin: 16px 24px;
          border-radius: 8px;
        }

        .messages-container {
          padding: 24px;
          height: 400px;
          overflow-y: auto;
          background: #f9fafb;
        }

        .message {
          margin-bottom: 16px;
          padding: 12px;
          border-radius: 8px;
          background: white;
          border-left: 3px solid #d1d5db;
        }

        .message-transcript {
          border-left-color: #3b82f6;
        }

        .message-agent_response {
          border-left-color: #10b981;
        }

        .message-type {
          display: inline-block;
          font-size: 11px;
          font-weight: 600;
          text-transform: uppercase;
          color: #6b7280;
          margin-bottom: 4px;
        }

        .message-content {
          color: #111827;
          line-height: 1.5;
        }

        .timestamp {
          display: block;
          margin-top: 4px;
          font-size: 11px;
          color: #9ca3af;
        }

        .input-area {
          display: flex;
          gap: 12px;
          padding: 24px;
          border-top: 1px solid #e5e7eb;
        }

        input {
          flex: 1;
          padding: 12px;
          border: 1px solid #d1d5db;
          border-radius: 8px;
          font-size: 14px;
        }

        .call-controls {
          padding: 0 24px 24px;
          text-align: center;
        }

        .info-box {
          background: #fef3c7;
          border-top: 1px solid #fde68a;
          padding: 16px 24px;
          font-size: 13px;
          color: #92400e;
        }

        .info-box p {
          margin: 0 0 8px 0;
        }

        .info-box ul {
          margin: 0;
          padding-left: 20px;
        }

        .info-box li {
          margin-bottom: 4px;
        }

        .btn {
          padding: 12px 32px;
          border-radius: 8px;
          font-size: 16px;
          font-weight: 500;
          border: none;
          cursor: pointer;
          transition: all 0.2s;
        }

        .btn-primary {
          background: #3b82f6;
          color: white;
        }

        .btn-primary:hover:not(:disabled) {
          background: #2563eb;
        }

        .btn-primary:disabled {
          background: #93c5fd;
          cursor: not-allowed;
        }

        .btn-danger {
          background: #ef4444;
          color: white;
        }

        .btn-danger:hover {
          background: #dc2626;
        }
      `}</style>
        </div>
    );
}
