'use client'

import {
  ResponsiveContainer,
  Cell,
  Tooltip,
  Legend,
} from 'recharts'
import { format } from 'date-fns'

interface HeatmapDataPoint {
  date: string
  hour: number
  value: number
}

interface HeatmapChartProps {
  data: HeatmapDataPoint[]
  height?: number
}

export function HeatmapChart({
  data,
  height = 400,
}: HeatmapChartProps) {
  // Transform data for heatmap visualization
  const transformedData = data.reduce((acc, point) => {
    const key = `${point.date}-${point.hour}`
    if (!acc[key]) {
      acc[key] = {
        date: point.date,
        hour: point.hour,
        value: 0,
      }
    }
    acc[key].value += point.value
    return acc
  }, {} as Record<string, HeatmapDataPoint>)

  const maxValue = Math.max(...Object.values(transformedData).map(d => d.value))
  const minValue = Math.min(...Object.values(transformedData).map(d => d.value))

  const getColor = (value: number) => {
    if (maxValue === minValue) return '#e5e7eb'
    const ratio = (value - minValue) / (maxValue - minValue)
    if (ratio < 0.25) return '#dbeafe'
    if (ratio < 0.5) return '#93c5fd'
    if (ratio < 0.75) return '#3b82f6'
    return '#1e40af'
  }

  const hours = Array.from({ length: 24 }, (_, i) => i)
  const dates = Array.from(new Set(data.map(d => d.date))).sort()

  return (
    <div className="w-full" style={{ height }}>
      <div className="grid grid-cols-25 gap-1">
        <div className="text-xs font-medium p-2">Hour</div>
        {dates.map(date => (
          <div key={date} className="text-xs text-center p-1">
            {format(new Date(date), 'MM/dd')}
          </div>
        ))}
        {hours.map(hour => (
          <div key={hour} className="contents">
            <div className="text-xs font-medium p-2">{hour}:00</div>
            {dates.map(date => {
              const key = `${date}-${hour}`
              const point = transformedData[key]
              const value = point?.value || 0
              return (
                <div
                  key={key}
                  className="rounded-sm p-1 text-xs text-center"
                  style={{
                    backgroundColor: getColor(value),
                    color: value > (maxValue + minValue) / 2 ? 'white' : 'black',
                  }}
                  title={`${date} ${hour}:00 - ${value}`}
                >
                  {value > 0 ? value : ''}
                </div>
              )
            })}
          </div>
        ))}
      </div>
      <div className="mt-4 flex items-center justify-center gap-2">
        <span className="text-xs">Less</span>
        <div className="flex gap-1">
          {[0, 0.25, 0.5, 0.75, 1].map(ratio => (
            <div
              key={ratio}
              className="w-4 h-4 rounded-sm"
              style={{
                backgroundColor: getColor(minValue + (maxValue - minValue) * ratio),
              }}
            />
          ))}
        </div>
        <span className="text-xs">More</span>
      </div>
    </div>
  )
}
