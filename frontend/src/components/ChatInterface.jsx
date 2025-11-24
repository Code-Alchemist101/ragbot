import { useState, useEffect, useRef } from 'react'

function ChatInterface({ bot, onBack }) {
    const [sessions, setSessions] = useState([])
    const [currentSession, setCurrentSession] = useState(null)
    const [messages, setMessages] = useState([])
    const [inputValue, setInputValue] = useState('')
    const [isLoading, setIsLoading] = useState(false)
    const messagesEndRef = useRef(null)

    // Fetch sessions for this bot
    useEffect(() => {
        fetchSessions()
    }, [bot])

    // Load messages when session changes
    useEffect(() => {
        if (currentSession) {
            loadHistory(currentSession)
        }
    }, [currentSession])

    // Auto-scroll to bottom
    useEffect(() => {
        scrollToBottom()
    }, [messages])

    const fetchSessions = async () => {
        try {
            const response = await fetch(`/api/bots/${bot.bot_id}/sessions`)
            const data = await response.json()
            const sessionIds = data.sessions || []
            setSessions(sessionIds)

            // Auto-select first session or create new one
            if (sessionIds.length > 0) {
                setCurrentSession(sessionIds[0])
            } else {
                createNewSession()
            }
        } catch (err) {
            console.error('Error fetching sessions:', err)
        }
    }

    const loadHistory = async (sessionId) => {
        try {
            const response = await fetch(`/api/history/${sessionId}`)
            const data = await response.json()
            setMessages(data.history || [])
        } catch (err) {
            console.error('Error loading history:', err)
            setMessages([])
        }
    }

    const createNewSession = () => {
        const newSessionId = generateUUID()
        setSessions([newSessionId, ...sessions])
        setCurrentSession(newSessionId)
        setMessages([])
    }

    const generateUUID = () => {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
            const r = Math.random() * 16 | 0
            const v = c === 'x' ? r : (r & 0x3 | 0x8)
            return v.toString(16)
        })
    }

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }

    const sendMessage = async () => {
        if (!inputValue.trim() || isLoading) return

        const question = inputValue.trim()
        setInputValue('')
        setIsLoading(true)

        // Add user message to UI
        const userMessage = {
            role: 'user',
            content: question,
            timestamp: new Date().toISOString()
        }
        setMessages(prev => [...prev, userMessage])

        try {
            // Use streaming endpoint
            const response = await fetch('/api/chat/stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question,
                    session_id: currentSession,
                    bot_id: bot.bot_id
                })
            })

            const reader = response.body.getReader()
            const decoder = new TextDecoder()
            let assistantMessage = ''

            // Add empty assistant message
            const assistantMsgIndex = messages.length + 1
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: '',
                timestamp: new Date().toISOString()
            }])

            while (true) {
                const { done, value } = await reader.read()
                if (done) break

                const chunk = decoder.decode(value)
                const lines = chunk.split('\n')

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6)
                        if (data === '[DONE]') break
                        if (data.startsWith('[ERROR]')) {
                            console.error('Streaming error:', data)
                            break
                        }

                        assistantMessage += data

                        // Update assistant message in real-time
                        setMessages(prev => {
                            const newMessages = [...prev]
                            newMessages[assistantMsgIndex] = {
                                role: 'assistant',
                                content: assistantMessage,
                                timestamp: new Date().toISOString()
                            }
                            return newMessages
                        })
                    }
                }
            }

            setIsLoading(false)
        } catch (err) {
            console.error('Error sending message:', err)
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: 'Sorry, an error occurred. Please try again.',
                timestamp: new Date().toISOString()
            }])
            setIsLoading(false)
        }
    }

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            sendMessage()
        }
    }

    return (
        <div className="chat-interface">
            {/* Sidebar */}
            <div className="chat-sidebar">
                <div className="sidebar-header">
                    <button className="back-button" onClick={onBack}>← Dashboard</button>
                    <div className="bot-info">
                        <h3>{bot.name}</h3>
                        <p className="bot-url">{bot.base_url}</p>
                    </div>
                </div>

                <div className="sessions-section">
                    <div className="sessions-header">
                        <h4>Conversations</h4>
                        <button className="new-chat-button" onClick={createNewSession}>
                            + New Chat
                        </button>
                    </div>

                    <div className="sessions-list">
                        {sessions.map((sessionId, index) => (
                            <div
                                key={sessionId}
                                className={`session-item ${sessionId === currentSession ? 'active' : ''}`}
                                onClick={() => setCurrentSession(sessionId)}
                            >
                                <span className="session-icon">💬</span>
                                <span className="session-name">Chat {sessions.length - index}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Chat Area */}
            <div className="chat-main">
                <div className="messages-container">
                    {messages.length === 0 ? (
                        <div className="empty-chat">
                            <h2>👋 Start a conversation</h2>
                            <p>Ask me anything about {bot.name}</p>
                        </div>
                    ) : (
                        messages.map((msg, index) => (
                            <div key={index} className={`message ${msg.role}`}>
                                <div className="message-avatar">
                                    {msg.role === 'user' ? '👤' : '🤖'}
                                </div>
                                <div className="message-content">
                                    <div className="message-text">{msg.content}</div>
                                    <div className="message-time">
                                        {new Date(msg.timestamp).toLocaleTimeString()}
                                    </div>
                                </div>
                            </div>
                        ))
                    )}
                    {isLoading && (
                        <div className="message assistant">
                            <div className="message-avatar">🤖</div>
                            <div className="message-content">
                                <div className="typing-indicator">
                                    <span></span>
                                    <span></span>
                                    <span></span>
                                </div>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                <div className="input-container">
                    <textarea
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder="Type your message... (Enter to send, Shift+Enter for new line)"
                        className="message-input"
                        rows="1"
                        disabled={isLoading}
                    />
                    <button
                        onClick={sendMessage}
                        disabled={!inputValue.trim() || isLoading}
                        className="send-button"
                    >
                        {isLoading ? '⏳' : '📤'}
                    </button>
                </div>
            </div>
        </div>
    )
}

export default ChatInterface
