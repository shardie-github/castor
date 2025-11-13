'use client'

import {
  FunnelChart,
  Funnel,
  LabelList,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'

interface FunnelDataPoint {
  name: string
  value: number
  fill?: string
}

interface FunnelChartProps {
  data: FunnelDataPoint[]
  height?: number
  colors?: string[]
}

export function FunnelChartComponent({
  data,
  height = 400,
  colors = ['#3b82f6', '#60a5fa', '#93c5fd', '#cbd5e1'],
}: FunnelChartProps) {
  const maxValue = Math.max(...data.map(d => d.value))

  return (
    <ResponsiveContainer width="100%" height={height}>
      <FunnelChart>
        <Tooltip
          contentStyle={{
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
          }}
        />
        <Funnel
          dataKey="value"
          data={data}
          isAnimationActive
        >
          {data.map((entry, index) => (
            <Cell
              key={`cell-${index}`}
              fill={entry.fill || colors[index % colors.length]}
            />
          ))}
          <LabelList
            position="right"
            fill="#000"
            stroke="none"
            dataKey="name"
            formatter={(value: string, entry: FunnelDataPoint) =>
              `${value}: ${entry.value.toLocaleString()}`
            }
          />
        </Funnel>
      </FunnelChart>
    </ResponsiveContainer>
  )
}
