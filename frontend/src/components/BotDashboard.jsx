import { useState, useEffect } from 'react'

function BotDashboard({ onAddBot, onSelectBot }) {
    const [bots, setBots] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    const handleDeleteBot = async (e, botId) => {
        e.stopPropagation() // Prevent card click
        if (!window.confirm('Are you sure you want to delete this bot? This action cannot be undone.')) {
            return
        }

        try {
            const response = await fetch(`/api/bots/${botId}`, {
                method: 'DELETE'
            })

            if (response.ok) {
                setBots(bots.filter(b => b.bot_id !== botId))
            } else {
                setError('Failed to delete bot')
            }
        } catch (err) {
            console.error('Error deleting bot:', err)
            setError('Failed to delete bot')
        }
    }

    const fetchBots = async () => {
        try {
            const response = await fetch('/api/bots')
            const data = await response.json()
            setBots(data.bots || [])
            setLoading(false)
        } catch (err) {
            console.error('Error fetching bots:', err)
            setError('Failed to load bots')
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchBots()

        // Auto-refresh every 30 seconds
        const interval = setInterval(fetchBots, 30000)
        return () => clearInterval(interval)
    }, [])

    if (loading) {
        return (
            <div className="dashboard-container">
                <div className="loading">Loading bots...</div>
            </div>
        )
    }

    return (
        <div className="dashboard-container">
            <div className="dashboard-header">
                <h1>🤖 RAG Chatbot Dashboard</h1>
                <p>Manage your intelligent website assistants</p>
            </div>

            {error && <div className="error-message">{error}</div>}

            <div className="bots-grid">
                {/* Add New Bot Card */}
                <div className="bot-card add-bot-card" onClick={onAddBot}>
                    <div className="add-bot-icon">+</div>
                    <h3>Add New Bot</h3>
                    <p>Crawl a new website</p>
                </div>

                {/* Existing Bots */}
                {bots.map((bot) => (
                    <div
                        key={bot.bot_id}
                        className="bot-card"
                        onClick={() => onSelectBot(bot)}
                    >
                        <div className="bot-icon">🤖</div>
                        <h3>{bot.name}</h3>
                        <p className="bot-url">{bot.base_url}</p>
                        <p className="bot-date">
                            Created: {new Date(bot.created_at).toLocaleDateString()}
                        </p>
                        <button
                            className="delete-bot-btn"
                            onClick={(e) => handleDeleteBot(e, bot.bot_id)}
                            title="Delete Bot"
                        >
                            🗑️
                        </button>
                    </div>
                ))}
            </div>

            {bots.length === 0 && !error && (
                <div className="empty-state">
                    <p>No bots yet. Create your first bot to get started!</p>
                </div>
            )}
        </div>
    )
}

export default BotDashboard
