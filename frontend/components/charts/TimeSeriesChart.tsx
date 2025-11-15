'use client'

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

interface TimeSeriesChartProps {
  data: Array<{
    date: string
    value: number
    [key: string]: string | number
  }>
  dataKeys: string[]
  xAxisKey?: string
  colors?: string[]
  height?: number
}

export function TimeSeriesChart({
  data,
  dataKeys,
  xAxisKey = 'date',
  colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444'],
  height = 400,
}: TimeSeriesChartProps) {
  // Mobile detection
  const isMobile = typeof window !== 'undefined' && window.innerWidth < 768

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: isMobile ? 60 : 40 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis
          dataKey={xAxisKey}
          tick={{ fontSize: isMobile ? 10 : 12 }}
          angle={isMobile ? -90 : -45}
          textAnchor={isMobile ? 'middle' : 'end'}
          height={isMobile ? 100 : 80}
          interval={isMobile ? 'preserveStartEnd' : 0}
        />
        <YAxis 
          tick={{ fontSize: isMobile ? 10 : 12 }}
          width={isMobile ? 40 : 60}
          tickFormatter={(value) => {
            if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`
            if (value >= 1000) return `${(value / 1000).toFixed(1)}K`
            return value.toString()
          }}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: 'rgba(255, 255, 255, 0.98)',
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
            padding: '8px',
            fontSize: isMobile ? '12px' : '14px',
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
          }}
          labelStyle={{ fontWeight: 'bold', marginBottom: '4px' }}
        />
        <Legend 
          wrapperStyle={{ fontSize: isMobile ? '12px' : '14px', paddingTop: '10px' }}
          iconType="line"
        />
        {dataKeys.map((key, index) => (
          <Line
            key={key}
            type="monotone"
            dataKey={key}
            stroke={colors[index % colors.length]}
            strokeWidth={isMobile ? 2 : 2.5}
            dot={{ r: isMobile ? 2 : 3 }}
            activeDot={{ r: isMobile ? 4 : 6 }}
            name={key.charAt(0).toUpperCase() + key.slice(1).replace(/([A-Z])/g, ' $1').trim()}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  )
}
