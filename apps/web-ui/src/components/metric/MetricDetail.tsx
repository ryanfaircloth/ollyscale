import { Modal, Badge, Tabs, Tab } from 'react-bootstrap';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale,
} from 'chart.js';
import 'chartjs-adapter-date-fns';
import { CopyButton } from '@/components/common/CopyButton';
import { formatTimestamp, formatNumber } from '@/utils/formatting';
import type { Metric } from '@/api/types/metric';

// Register Chart.js components
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, TimeScale);

interface MetricDetailProps {
  metric: Metric | null;
  onHide: () => void;
}

export function MetricDetail({ metric, onHide }: MetricDetailProps) {
  if (!metric) return null;

  const getMetricTypeBadge = (type: string) => {
    const typeMap: Record<string, string> = {
      Gauge: 'primary',
      Counter: 'success',
      Histogram: 'info',
      Summary: 'warning',
    };
    const variant = typeMap[type] || 'secondary';
    return <Badge bg={variant}>{type}</Badge>;
  };

  // Prepare chart data
  const chartData = {
    labels: metric.data_points.map((dp) =>
      new Date(dp.time ? dp.time / 1_000_000 : 0)
    ),
    datasets: [
      {
        label: metric.name,
        data: metric.data_points.map((dp) => dp.value ?? dp.sum ?? dp.count ?? 0),
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        tension: 0.1,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      title: {
        display: false,
      },
      tooltip: {
        callbacks: {
          label: (context: any) => {
            let label = context.dataset.label || '';
            if (label) {
              label += ': ';
            }
            if (context.parsed.y !== null) {
              label += formatNumber(context.parsed.y);
            }
            if (metric.unit) {
              label += ` ${metric.unit}`;
            }
            return label;
          },
        },
      },
    },
    scales: {
      x: {
        type: 'time' as const,
        time: {
          displayFormats: {
            millisecond: 'HH:mm:ss.SSS',
            second: 'HH:mm:ss',
            minute: 'HH:mm',
            hour: 'HH:mm',
          },
        },
        title: {
          display: true,
          text: 'Time',
        },
      },
      y: {
        title: {
          display: true,
          text: metric.unit || 'Value',
        },
      },
    },
  };

  // Get latest value
  const latestDataPoint = metric.data_points[metric.data_points.length - 1];
  const latestValue = latestDataPoint?.value ?? '-';

  return (
    <Modal show={true} onHide={onHide} size="xl" centered>
      <Modal.Header closeButton>
        <Modal.Title>
          <span className="me-2">{metric.name}</span>
          {getMetricTypeBadge(metric.type)}
        </Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <Tabs defaultActiveKey="overview" className="mb-3">
          {/* Overview Tab */}
          <Tab eventKey="overview" title="Overview">
            <div className="row mb-3">
              <div className="col-md-6">
                <h6 className="mb-2">Metric Information</h6>
                <table className="table table-sm table-borderless">
                  <tbody>
                    <tr>
                      <td className="text-muted" style={{ width: '150px' }}>
                        Name:
                      </td>
                      <td>
                        <strong>{metric.name}</strong>
                        <CopyButton text={metric.name} className="ms-2" />
                      </td>
                    </tr>
                    <tr>
                      <td className="text-muted">Type:</td>
                      <td>{getMetricTypeBadge(metric.type)}</td>
                    </tr>
                    {metric.unit && (
                      <tr>
                        <td className="text-muted">Unit:</td>
                        <td>
                          <code>{metric.unit}</code>
                        </td>
                      </tr>
                    )}
                    {metric.description && (
                      <tr>
                        <td className="text-muted">Description:</td>
                        <td>{metric.description}</td>
                      </tr>
                    )}
                    <tr>
                      <td className="text-muted">Data Points:</td>
                      <td>
                        <Badge bg="info">{metric.data_points.length}</Badge>
                      </td>
                    </tr>
                    <tr>
                      <td className="text-muted">Latest Value:</td>
                      <td>
                        <code className="fs-5">{formatNumber(latestValue as number)}</code>
                        {metric.unit && <span className="ms-2 text-muted">{metric.unit}</span>}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div className="col-md-6">
                {metric.attributes && Object.keys(metric.attributes).length > 0 && (
                  <>
                    <h6 className="mb-2">Metric Attributes</h6>
                    <div
                      className="bg-white p-2 rounded border"
                      style={{ maxHeight: '150px', overflow: 'auto' }}
                    >
                      <table className="table table-sm table-borderless mb-0">
                        <tbody>
                          {Object.entries(metric.attributes).slice(0, 5).map(([key, value]) => (
                            <tr key={key}>
                              <td className="text-muted small" style={{ width: '40%' }}>
                                {key}
                              </td>
                              <td className="small">
                                <code>{typeof value === 'string' ? value : JSON.stringify(value)}</code>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* Time Series Chart */}
            <h6 className="mb-2">Time Series</h6>
            <div style={{ height: '400px' }}>
              <Line data={chartData} options={chartOptions} />
            </div>
          </Tab>

          {/* Attributes Tab */}
          <Tab eventKey="attributes" title="Attributes">
            {metric.attributes && Object.keys(metric.attributes).length > 0 ? (
              <div style={{ maxHeight: '500px', overflow: 'auto' }}>
                <table className="table table-sm table-hover">
                  <thead>
                    <tr>
                      <th>Key</th>
                      <th>Value</th>
                      <th style={{ width: '80px' }}></th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(metric.attributes).map(([key, value]) => (
                      <tr key={key}>
                        <td className="text-muted">{key}</td>
                        <td>
                          <code>{typeof value === 'string' ? value : JSON.stringify(value)}</code>
                        </td>
                        <td>
                          <CopyButton text={typeof value === 'string' ? value : JSON.stringify(value)} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center text-muted py-4">No attributes</div>
            )}
          </Tab>

          {/* Data Points Tab */}
          <Tab eventKey="datapoints" title="Data Points">
            <div style={{ maxHeight: '500px', overflow: 'auto' }}>
              <table className="table table-sm table-hover">
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>Value</th>
                  </tr>
                </thead>
                <tbody>
                  {[...metric.data_points].reverse().map((dp, index) => (
                    <tr key={index}>
                      <td className="small">
                        {formatTimestamp(dp.time ? new Date(dp.time / 1_000_000).toISOString() : new Date().toISOString())}
                      </td>
                      <td>
                        <code>{formatNumber(dp.value ?? dp.sum ?? dp.count ?? 0)}</code>
                        {metric.unit && <span className="ms-2 text-muted">{metric.unit}</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Tab>
        </Tabs>
      </Modal.Body>
    </Modal>
  );
}
