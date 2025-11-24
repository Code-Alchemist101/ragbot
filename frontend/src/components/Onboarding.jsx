import { useState } from 'react'

function Onboarding({ onBotCreated, onBack }) {
    const [url, setUrl] = useState('')
    const [depth, setDepth] = useState(2)
    const [chunkSize, setChunkSize] = useState(500)
    const [chunkOverlap, setChunkOverlap] = useState(100)
    const [showAdvanced, setShowAdvanced] = useState(false)
    const [crawling, setCrawling] = useState(false)
    const [progress, setProgress] = useState(null)
    const [error, setError] = useState(null)

    const isValidUrl = (string) => {
        try {
            new URL(string)
            return true
        } catch (_) {
            return false
        }
    }

    const startCrawl = async () => {
        if (!url || !isValidUrl(url)) {
            setError('Please enter a valid URL')
            return
        }

        setCrawling(true)
        setError(null)
        setProgress({ stage: 'initializing', progress: {} })

        try {
            // Start crawl
            const response = await fetch('/api/crawl', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    url,
                    depth,
                    chunk_size: chunkSize,
                    chunk_overlap: chunkOverlap
                })
            })

            const data = await response.json()
            const crawlId = data.crawl_id

            // Listen to SSE stream for progress
            const eventSource = new EventSource(`/api/crawl/stream/${crawlId}`)

            eventSource.onmessage = (event) => {
                const update = JSON.parse(event.data)
                setProgress(update)

                if (update.status === 'completed') {
                    eventSource.close()

                    // Create bot
                    const result = update.result
                    if (result && result.success) {
                        createBot(result.namespace, url)
                    } else {
                        setError('Crawl completed but failed to index content')
                        setCrawling(false)
                    }
                } else if (update.status === 'failed') {
                    eventSource.close()
                    setError(update.error || 'Crawl failed')
                    setCrawling(false)
                }
            }

            eventSource.onerror = (err) => {
                console.error('SSE error:', err)
                eventSource.close()
                setError('Connection error. Please try again.')
                setCrawling(false)
            }

        } catch (err) {
            console.error('Error starting crawl:', err)
            setError('Failed to start crawl')
            setCrawling(false)
        }
    }

    const createBot = async (namespace, baseUrl) => {
        try {
            const botName = new URL(baseUrl).hostname

            const response = await fetch('/api/bots', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: botName,
                    namespace: namespace,
                    base_url: baseUrl
                })
            })

            const bot = await response.json()
            setCrawling(false)
            onBotCreated(bot)
        } catch (err) {
            console.error('Error creating bot:', err)
            setError('Failed to create bot profile')
            setCrawling(false)
        }
    }

    const getStageLabel = (stage) => {
        const labels = {
            'initializing': 'Initializing...',
            'url_discovery': 'Discovering URLs',
            'deduplication_check': 'Checking for duplicates',
            'content_extraction': 'Extracting content',
            'metadata_tagging': 'Tagging metadata',
            'chunking': 'Chunking documents',
            'indexing': 'Indexing to vector database',
            'completed': 'Completed!'
        }
        return labels[stage] || stage
    }

    const getProgressPercentage = () => {
        if (!progress) return 0

        const stages = ['initializing', 'url_discovery', 'deduplication_check', 'content_extraction', 'metadata_tagging', 'chunking', 'indexing', 'completed']
        const currentIndex = stages.indexOf(progress.stage)
        return ((currentIndex + 1) / stages.length) * 100
    }

    return (
        <div className="onboarding-container">
            <div className="onboarding-card">
                <button className="back-button" onClick={onBack}>← Back</button>

                <h1>🚀 Add New Bot</h1>
                <p>Enter a website URL to crawl and create an intelligent chatbot</p>

                {!crawling ? (
                    <div className="onboarding-form">
                        <div className="form-group">
                            <label htmlFor="url">Website URL</label>
                            <input
                                id="url"
                                type="text"
                                placeholder="https://example.com"
                                value={url}
                                onChange={(e) => setUrl(e.target.value)}
                                className="url-input"
                            />
                        </div>

                        <div className="form-group">
                            <label htmlFor="depth">Crawl Depth</label>
                            <select
                                id="depth"
                                value={depth}
                                onChange={(e) => setDepth(Number(e.target.value))}
                                className="depth-select"
                            >
                                <option value={1}>1 - Fast (fewer pages)</option>
                                <option value={2}>2 - Balanced (recommended)</option>
                                <option value={3}>3 - Deep</option>
                                <option value={4}>4 - Very Deep</option>
                                <option value={5}>5 - Maximum</option>
                            </select>
                        </div>

                        <div className="advanced-settings">
                            <button
                                className="advanced-toggle"
                                onClick={() => setShowAdvanced(!showAdvanced)}
                            >
                                {showAdvanced ? '▼' : '▶'} Advanced Settings
                            </button>

                            {showAdvanced && (
                                <div className="settings-grid">
                                    <div className="form-group">
                                        <label htmlFor="chunkSize">Chunk Size (chars)</label>
                                        <input
                                            id="chunkSize"
                                            type="number"
                                            min="100"
                                            max="2000"
                                            value={chunkSize}
                                            onChange={(e) => setChunkSize(Number(e.target.value))}
                                            className="depth-select"
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label htmlFor="chunkOverlap">Overlap (chars)</label>
                                        <input
                                            id="chunkOverlap"
                                            type="number"
                                            min="0"
                                            max="500"
                                            value={chunkOverlap}
                                            onChange={(e) => setChunkOverlap(Number(e.target.value))}
                                            className="depth-select"
                                        />
                                    </div>
                                </div>
                            )}
                        </div>

                        {error && <div className="error-message">{error}</div>}

                        <button
                            className="start-button"
                            onClick={startCrawl}
                            disabled={!url}
                        >
                            Start Crawling
                        </button>
                    </div>
                ) : (
                    <div className="progress-container">
                        <div className="progress-stage">
                            <h3>{getStageLabel(progress?.stage)}</h3>
                        </div>

                        <div className="progress-bar">
                            <div
                                className="progress-fill"
                                style={{ width: `${getProgressPercentage()}%` }}
                            />
                        </div>

                        <div className="progress-stats">
                            {progress?.progress?.urls_discovered && (
                                <div className="stat">
                                    <span className="stat-label">URLs Discovered:</span>
                                    <span className="stat-value">{progress.progress.urls_discovered}</span>
                                </div>
                            )}
                            {progress?.progress?.documents_extracted && (
                                <div className="stat">
                                    <span className="stat-label">Documents Extracted:</span>
                                    <span className="stat-value">{progress.progress.documents_extracted}</span>
                                </div>
                            )}
                            {progress?.progress?.chunks_created && (
                                <div className="stat">
                                    <span className="stat-label">Chunks Created:</span>
                                    <span className="stat-value">{progress.progress.chunks_created}</span>
                                </div>
                            )}
                            {progress?.result?.indexed_documents && (
                                <div className="stat">
                                    <span className="stat-label">Documents Indexed:</span>
                                    <span className="stat-value">{progress.result.indexed_documents}</span>
                                </div>
                            )}
                        </div>

                        {progress?.status === 'completed' && (
                            <div className="success-message">
                                ✓ Crawl completed successfully! Creating bot...
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    )
}

export default Onboarding
