import {
  Area,
  AreaChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { CgmReading } from '../types/twin'

function timeLabel(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

export function GlucoseChart({ readings }: { readings: CgmReading[] }) {
  const data = readings.map((reading) => ({
    ...reading,
    time: timeLabel(reading.observedAt),
  }))

  if (!data.length) {
    return <div className="chart-empty">No CGM readings are available yet.</div>
  }

  return (
    <div className="chart" aria-label="Continuous glucose history chart">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 12, left: -22, bottom: 0 }}>
          <defs>
            <linearGradient id="glucoseFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#25d09a" stopOpacity={0.35} />
              <stop offset="100%" stopColor="#25d09a" stopOpacity={0.01} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="#dfe9e6" strokeDasharray="4 6" vertical={false} />
          <XAxis dataKey="time" tickLine={false} axisLine={false} minTickGap={24} tick={{ fill: '#657a74', fontSize: 12 }} />
          <YAxis domain={['dataMin - 15', 'dataMax + 25']} tickLine={false} axisLine={false} tick={{ fill: '#657a74', fontSize: 12 }} />
          <Tooltip
            cursor={{ stroke: '#8aa29b', strokeDasharray: '4 4' }}
            formatter={(value) => [`${Number(value).toFixed(0)} mg/dL`, 'Glucose']}
            labelFormatter={(label) => `Observed at ${label}`}
            contentStyle={{ borderRadius: 12, borderColor: '#dce9e5', boxShadow: '0 12px 30px rgba(15, 44, 37, .12)' }}
          />
          <ReferenceLine y={180} stroke="#f1a55b" strokeDasharray="5 5" label={{ value: '180', fill: '#a65b1d', fontSize: 11 }} />
          <Area type="monotone" dataKey="glucoseMgDl" stroke="#07966b" strokeWidth={3} fill="url(#glucoseFill)" activeDot={{ r: 5, fill: '#071816' }} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
