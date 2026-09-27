export default function MessageBubble({ text, sender, options, onSelect }) {
  return (
    <div className={`message-wrap ${sender}`}>
      <div className={`bubble ${sender}`}>
        {text}
      </div>

      {sender === 'agent' && options?.length > 0 && (
        <div className="option-cards">
          {options.map((option, index) => {
            const name = option.name || option.title || `Option ${index + 1}`

            return (
              <div className="option-card" key={index}>
                <div className="option-icon">
                  {option.mode === 'flight' || option.mode === 'train' || option.mode === 'bus'
                    ? '🚆'
                    : option.price_per_night
                    ? '🏨'
                    : '✈️'}
                </div>

                <div className="option-info">
                  <strong>{name}</strong>

                  <span>
                    {option.mode && `${option.mode} • `}
                    {option.price_per_night
                      ? `₹${option.price_per_night}/night`
                      : option.price
                      ? `₹${option.price}`
                      : ''}
                  </span>

                  {option.duration && (
                    <small>{option.duration}</small>
                  )}

                  {option.rating && (
                    <small>⭐ {option.rating}</small>
                  )}
                </div>

                <button onClick={() => onSelect(name)}>
                  Select
                </button>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}