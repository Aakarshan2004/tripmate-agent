import { useState } from 'react'
import ChatWindow from './components/ChatWindow'
import InputBar from './components/InputBar'

const threadId = 'user-' + Math.random().toString(36).slice(2)

const suggestions = [
  'Delhi → Goa',
  'Mumbai → Manali',
  'Budget trip',
  'Weekend getaway',
]

export default function App() {
  const [messages, setMessages] = useState([
    {
      sender: 'agent',
      text: "Hi! Tell me where you want to go and when, and I'll plan your whole trip.",
    },
  ])

  const [started, setStarted] = useState(false)
  const [completed, setCompleted] = useState(false)
  const [loading, setLoading] = useState(false)

  async function handleSend(text) {
    if (!text?.trim() || loading || completed) return

    setMessages((prev) => [
      ...prev,
      {
        sender: 'user',
        text,
      },
    ])

    setLoading(true)

    try {
      const endpoint = started
        ? '/trip/resume'
        : '/trip/start'

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: text,
          thread_id: threadId,
        }),
      })

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`)
      }

      const data = await response.json()

      setStarted(true)

      // Agent is waiting for user's next input
      if (data.status === 'waiting_for_input') {
        setMessages((prev) => [
          ...prev,
          {
            sender: 'agent',
            text: data.question,
            options: data.options || [],
          },
        ])
      }

      // Trip successfully completed
      else if (data.status === 'completed') {
        setCompleted(true)

        const budget = data.final_state?.budget
        const itinerary = data.final_state?.itinerary

        let summary = '🎉 Trip planning complete!\n\n'

        if (itinerary?.length) {
          summary += '🗺️ Itinerary\n\n'
          summary += itinerary.join('\n')
          summary += '\n\n'
        }

        if (budget) {
          summary += `💰 Total budget: ₹${budget.total}`
        }

        setMessages((prev) => [
          ...prev,
          {
            sender: 'agent',
            text: summary,
          },
        ])
      }

      // Trip cancelled
      else if (data.status === 'cancelled') {
        setCompleted(true)

        setMessages((prev) => [
          ...prev,
          {
            sender: 'agent',
            text:
              '❌ Trip planning cancelled.\n\nRefresh the page to start a new trip.',
          },
        ])
      }
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          sender: 'agent',
          text: '⚠️ ' + error.message,
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">

      {/* Header */}
      <header>
        <div className="brand">
          <div className="logo">🧳</div>

          <div>
            <h1>TripMate</h1>
            <p className="subtitle">
              Your AI trip planning agent
            </p>
          </div>
        </div>

        <div className="status-pill">
          <span className="status-dot"></span>
          AI Agent Online
        </div>
      </header>

      {/* Welcome section */}
      {!started && (
        <div className="welcome">
          <div className="welcome-icon">✈️</div>

          <h2>Plan your next adventure</h2>

          <p>
            Tell me your destination, dates and budget.
            I'll handle the rest.
          </p>

          <div className="suggestions">
            {suggestions.map((suggestion) => (
              <button
                key={suggestion}
                onClick={() => handleSend(suggestion)}
                disabled={loading}
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Chat */}
      <ChatWindow
        messages={messages}
        onSelect={handleSend}
      />

      {/* Loading */}
      {loading && (
        <div className="status thinking">
          <span></span>
          TripMate is thinking...
        </div>
      )}

      {/* Input */}
      <InputBar
        onSend={handleSend}
        disabled={loading || completed}
      />

      {/* Completed / Cancelled */}
      {completed && (
        <div className="status done">
          Trip planning finished ✅
        </div>
      )}

    </div>
  )
}