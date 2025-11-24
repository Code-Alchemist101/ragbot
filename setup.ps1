# Quick Setup Script for RAG Chatbot Application
# Run this script to set up the environment

Write-Host "🚀 RAG Chatbot Application - Quick Setup" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python 3.11+" -ForegroundColor Red
    exit 1
}

# Check Node.js
Write-Host "Checking Node.js installation..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version
    Write-Host "✓ Node.js found: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Node.js not found. Please install Node.js 18+" -ForegroundColor Red
    exit 1
}

# Check MongoDB
Write-Host "Checking MongoDB installation..." -ForegroundColor Yellow
try {
    $mongoVersion = mongod --version
    Write-Host "✓ MongoDB found" -ForegroundColor Green
} catch {
    Write-Host "⚠ MongoDB not found. Install MongoDB or use MongoDB Atlas" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Setting up Backend..." -ForegroundColor Cyan

# Backend setup
Set-Location backend

# Create virtual environment
Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
python -m venv venv

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Create .env file
if (-not (Test-Path .env)) {
    Write-Host "Creating .env file..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "⚠ Please edit backend/.env with your API keys!" -ForegroundColor Yellow
} else {
    Write-Host "✓ .env file already exists" -ForegroundColor Green
}

Set-Location ..

Write-Host ""
Write-Host "Setting up Frontend..." -ForegroundColor Cyan

# Frontend setup
Set-Location frontend

# Install dependencies
Write-Host "Installing Node.js dependencies..." -ForegroundColor Yellow
npm install

Set-Location ..

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "✓ Setup Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "1. Edit backend/.env with your API keys" -ForegroundColor White
Write-Host "   - GOOGLE_API_KEY (from https://makersuite.google.com/app/apikey)" -ForegroundColor White
Write-Host "   - PINECONE_API_KEY (from https://www.pinecone.io/)" -ForegroundColor White
Write-Host "   - PINECONE_INDEX (create index with dimension=768, metric=cosine)" -ForegroundColor White
Write-Host ""
Write-Host "2. Start MongoDB (if using local):" -ForegroundColor White
Write-Host "   mongod" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Start Backend:" -ForegroundColor White
Write-Host "   cd backend" -ForegroundColor Gray
Write-Host "   python app.py" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Start Frontend (in new terminal):" -ForegroundColor White
Write-Host "   cd frontend" -ForegroundColor Gray
Write-Host "   npm run dev" -ForegroundColor Gray
Write-Host ""
Write-Host "5. Open http://localhost:5173 in your browser" -ForegroundColor White
Write-Host ""
