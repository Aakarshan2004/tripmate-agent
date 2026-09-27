import { useState } from 'react'

export default function InputBar({ onSend, disabled }) {
  const [value, setValue] = useState('')

  function handleSubmit(e) {
    e.preventDefault()

    if (!value.trim() || disabled) return

    onSend(value.trim())
    setValue('')
  }

  return (
    <form className="input-bar" onSubmit={handleSubmit}>
      <input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Where do you want to travel?"
        disabled={disabled}
        autoComplete="off"
      />

      <button type="submit" disabled={disabled}>
        Send
      </button>
    </form>
  )
}