import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import type { MetricDataPoint } from '@/api/types/common';
import { formatTimestamp } from '@/utils/formatting';

interface MetricTimeSeriesChartProps {
  dataPoints: MetricDataPoint[];
  metricName: string;
  height?: number;
}

export function MetricTimeSeriesChart({ dataPoints, metricName, height = 300 }: MetricTimeSeriesChartProps) {
  if (!dataPoints || dataPoints.length === 0) {
    return (
      <div className="text-center text-muted py-5">
        <i className="bi bi-graph-down fs-1"></i>
        <p className="mt-2">No data points available</p>
      </div>
    );
  }

  // Transform data for Recharts
  const chartData = dataPoints.map((point) => ({
    timestamp: new Date(point.timestamp).getTime(),
    value: typeof point.value === 'number' ? point.value : parseFloat(String(point.value)),
    timeLabel: formatTimestamp(point.timestamp),
  }));

  // Sort by timestamp
  chartData.sort((a, b) => a.timestamp - b.timestamp);

  // Calculate min/max for better Y-axis scaling
  const values = chartData.map((d) => d.value);
  const minValue = Math.min(...values);
  const maxValue = Math.max(...values);
  const padding = (maxValue - minValue) * 0.1 || 1; // 10% padding

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />

        <XAxis
          dataKey="timestamp"
          type="number"
          domain={['dataMin', 'dataMax']}
          tickFormatter={(value) => formatTimestamp(new Date(value).toISOString())}
          stroke="#666"
          style={{ fontSize: '12px' }}
        />

        <YAxis
          domain={[Math.max(0, minValue - padding), maxValue + padding]}
          stroke="#666"
          style={{ fontSize: '12px' }}
          tickFormatter={(value) => {
            // Format large numbers with K/M/B suffix
            if (value >= 1000000000) return `${(value / 1000000000).toFixed(1)}B`;
            if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
            if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
            return value.toFixed(2);
          }}
        />

        <Tooltip
          contentStyle={{
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            border: '1px solid #ccc',
            borderRadius: '4px',
            padding: '8px',
          }}
          labelFormatter={(value) => formatTimestamp(new Date(value).toISOString())}
          formatter={(value) => (typeof value === 'number' ? value.toFixed(4) : String(value))}
        />

        <Legend
          wrapperStyle={{ fontSize: '14px' }}
          iconType="line"
        />

        <Line
          type="monotone"
          dataKey="value"
          name={metricName}
          stroke="#0d6efd"
          strokeWidth={2}
          dot={{ r: 3 }}
          activeDot={{ r: 5 }}
          animationDuration={500}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
