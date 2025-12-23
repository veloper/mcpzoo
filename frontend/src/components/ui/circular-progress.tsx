import * as React from "react"
import { cn } from "@/lib/utils"

interface CircularProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  progress: number // 0-100
  size?: number
  strokeWidth?: number
  showValue?: boolean
  valueClassName?: string
}

const CircularProgress = React.forwardRef<HTMLDivElement, CircularProgressProps>(
  ({ className, progress, size = 40, strokeWidth = 3, showValue = false, valueClassName, ...props }, ref) => {
    const normalizedRadius = (size - strokeWidth) / 2
    const circumference = normalizedRadius * 2 * Math.PI
    const strokeDasharray = `${circumference} ${circumference}`
    const strokeDashoffset = circumference - (progress / 100) * circumference

    return (
      <div
        ref={ref}
        className={cn("relative inline-flex items-center justify-center", className)}
        style={{ width: size, height: size }}
        {...props}
      >
        <svg
          width={size}
          height={size}
          className="transform -rotate-90"
        >
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={normalizedRadius}
            strokeWidth={strokeWidth}
            fill="transparent"
            stroke="currentColor"
            strokeOpacity={0.2}
          />
          {/* Progress circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={normalizedRadius}
            strokeWidth={strokeWidth}
            fill="transparent"
            stroke="currentColor"
            strokeDasharray={strokeDasharray}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-all duration-300 ease-in-out"
          />
        </svg>
        {showValue && (
          <div className={cn(
            "absolute inset-0 flex items-center justify-center text-xs font-medium",
            valueClassName
          )}>
            {Math.round(progress)}%
          </div>
        )}
      </div>
    )
  }
)

CircularProgress.displayName = "CircularProgress"

export { CircularProgress }
