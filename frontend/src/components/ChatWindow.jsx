import { useEffect, useRef } from 'react'
import MessageBubble from './MessageBubble'

export default function ChatWindow({ messages, onSelect }) {
  const endRef = useRef(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div className="chat-window">
      {messages.map((m, i) => (
        <MessageBubble
          key={i}
          text={m.text}
          sender={m.sender}
          options={m.options}
          onSelect={onSelect}
        />
      ))}

      <div ref={endRef} />
    </div>
  )
}