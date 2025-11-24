import { useState } from 'react'

function ChatWidget({ onClose }) {
    const [isExpanded, setIsExpanded] = useState(false)
    const [messages, setMessages] = useState([])
    const [inputValue, setInputValue] = useState('')

    const toggleWidget = () => {
        setIsExpanded(!isExpanded)
    }

    const sendMessage = () => {
        if (!inputValue.trim()) return

        const userMessage = {
            role: 'user',
            content: inputValue,
            timestamp: new Date().toISOString()
        }

        setMessages([...messages, userMessage])
        setInputValue('')

        // Simulate bot response (you can integrate with actual API)
        setTimeout(() => {
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: 'This is a demo response from the chat widget.',
                timestamp: new Date().toISOString()
            }])
        }, 1000)
    }

    return (
        <div className="chat-widget">
            {!isExpanded ? (
                <button className="widget-button" onClick={toggleWidget}>
                    💬
                </button>
            ) : (
                <div className="widget-expanded">
                    <div className="widget-header">
                        <h4>Chat Assistant</h4>
                        <button className="widget-close" onClick={toggleWidget}>✕</button>
                    </div>

                    <div className="widget-messages">
                        {messages.map((msg, index) => (
                            <div key={index} className={`widget-message ${msg.role}`}>
                                {msg.content}
                            </div>
                        ))}
                    </div>

                    <div className="widget-input">
                        <input
                            type="text"
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                            placeholder="Type a message..."
                        />
                        <button onClick={sendMessage}>Send</button>
                    </div>
                </div>
            )}
        </div>
    )
}

export default ChatWidget
