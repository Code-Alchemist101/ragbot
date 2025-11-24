import { useState } from 'react'
import BotDashboard from './components/BotDashboard'
import Onboarding from './components/Onboarding'
import ChatInterface from './components/ChatInterface'
import ChatWidget from './components/ChatWidget'

function App() {
    const [currentView, setCurrentView] = useState('dashboard') // 'dashboard', 'onboarding', 'chat'
    const [selectedBot, setSelectedBot] = useState(null)
    const [showChatWidget, setShowChatWidget] = useState(false)

    const handleAddBot = () => {
        setCurrentView('onboarding')
    }

    const handleBotCreated = (bot) => {
        setSelectedBot(bot)
        setCurrentView('chat')
    }

    const handleSelectBot = (bot) => {
        setSelectedBot(bot)
        setCurrentView('chat')
    }

    const handleBackToDashboard = () => {
        setCurrentView('dashboard')
        setSelectedBot(null)
    }

    return (
        <div className="app">
            {currentView === 'dashboard' && (
                <BotDashboard
                    onAddBot={handleAddBot}
                    onSelectBot={handleSelectBot}
                />
            )}

            {currentView === 'onboarding' && (
                <Onboarding
                    onBotCreated={handleBotCreated}
                    onBack={handleBackToDashboard}
                />
            )}

            {currentView === 'chat' && selectedBot && (
                <ChatInterface
                    bot={selectedBot}
                    onBack={handleBackToDashboard}
                />
            )}

            {/* Floating Chat Widget (optional) */}
            {showChatWidget && (
                <ChatWidget
                    onClose={() => setShowChatWidget(false)}
                />
            )}
        </div>
    )
}

export default App
