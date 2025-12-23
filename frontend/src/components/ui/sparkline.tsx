import React from 'react'

interface SparklineProps {
  data: number[]
  width?: number
  height?: number
  className?: string
}

export function Sparkline({ data, width = 50, height = 20, className }: SparklineProps) {
  if (data.length < 2) return null

  const min = Math.min(...data)
  const max = Math.max(...data)
  const range = max - min || 1

  const points = data.map((val, i) => {
    const x = (i / (data.length - 1)) * width
    const y = height - ((val - min) / range) * height
    return `${x},${y}`
  }).join(' ')

  return (
    <svg width={width} height={height} className={className}>
      <polyline
        fill="none"
        stroke="currentColor"
        strokeWidth="1"
        points={points}
        className="text-blue-500"
      />
    </svg>
  )
}