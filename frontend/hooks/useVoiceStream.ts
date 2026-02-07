import { useState, useEffect, useRef, useCallback } from 'react';

const FASTAPI_WS_URL = process.env.NEXT_PUBLIC_FASTAPI_WS_URL || 'ws://localhost:8001';

interface Message {
    type: string;
    text?: string;
    data?: string;
    timestamp?: string;
    is_final?: boolean;
    message?: string;
}

export function useVoiceStream(sessionId: string | null) {
    const [isConnected, setIsConnected] = useState(false);
    const [messages, setMessages] = useState<Message[]>([]);
    const [transcript, setTranscript] = useState<string>('');
    const [error, setError] = useState<string | null>(null);

    const wsRef = useRef<WebSocket | null>(null);
    const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

    const connect = useCallback(() => {
        if (!sessionId) return;

        try {
            const ws = new WebSocket(`${FASTAPI_WS_URL}/ws/voice/${sessionId}`);

            ws.onopen = () => {
                console.log('WebSocket connected');
                setIsConnected(true);
                setError(null);
            };

            ws.onmessage = (event) => {
                try {
                    const message: Message = JSON.parse(event.data);
                    console.log('Received message:', message);

                    setMessages((prev) => [...prev, message]);

                    // Handle different message types
                    switch (message.type) {
                        case 'transcript':
                            if (message.is_final) {
                                setTranscript(message.text || '');
                            }
                            break;
                        case 'agent_response':
                            // Agent response received
                            break;
                        case 'error':
                            setError(message.message || 'Unknown error');
                            break;
                    }
                } catch (e) {
                    console.error('Error parsing message:', e);
                }
            };

            ws.onerror = (event) => {
                console.error('WebSocket error:', event);
                setError('WebSocket connection error');
            };

            ws.onclose = () => {
                console.log('WebSocket disconnected');
                setIsConnected(false);

                // Attempt to reconnect after 3 seconds
                reconnectTimeoutRef.current = setTimeout(() => {
                    console.log('Attempting to reconnect...');
                    connect();
                }, 3000);
            };

            wsRef.current = ws;
        } catch (e) {
            console.error('Error creating WebSocket:', e);
            setError('Failed to create WebSocket connection');
        }
    }, [sessionId]);

    const disconnect = useCallback(() => {
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
        }

        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }

        setIsConnected(false);
    }, []);

    const sendMessage = useCallback((message: any) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify(message));
        } else {
            console.error('WebSocket is not open');
            setError('WebSocket is not connected');
        }
    }, []);

    const sendAudioChunk = useCallback((audioData: string) => {
        sendMessage({
            type: 'audio_chunk',
            data: audioData,
            timestamp: Date.now(),
        });
    }, [sendMessage]);

    const sendTextMessage = useCallback((text: string) => {
        sendMessage({
            type: 'text_message',
            text: text,
        });
    }, [sendMessage]);

    const endStream = useCallback(() => {
        sendMessage({ type: 'end_stream' });
        disconnect();
    }, [sendMessage, disconnect]);

    useEffect(() => {
        if (sessionId) {
            connect();
        }

        return () => {
            disconnect();
        };
    }, [sessionId, connect, disconnect]);

    return {
        isConnected,
        messages,
        transcript,
        error,
        sendAudioChunk,
        sendTextMessage,
        endStream,
        connect,
        disconnect,
    };
}
