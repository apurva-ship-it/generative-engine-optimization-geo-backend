import React from 'react'

interface ProgressBarProps {
  progress: number // 0-100
}

const ProgressBar: React.FC<ProgressBarProps> = ({ progress }) => {
  return (
    <div
      style={{
        width: '100%',
        backgroundColor: '#e0e0e0',
        borderRadius: 9999,
        height: 16,
        overflow: 'hidden',
        marginTop: 12,
      }}
    >
      <div
        style={{
          height: '100%',
          width: `${Math.min(100, Math.max(0, progress))}%`,
          backgroundColor: '#1976d2',
          borderRadius: 9999,
          transition: 'width 0.2s ease',
        }}
        role="progressbar"
        aria-valuenow={progress}
        aria-valuemin={0}
        aria-valuemax={100}
      />
    </div>
  )
}

export default ProgressBar
