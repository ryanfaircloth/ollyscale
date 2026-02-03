import { useHealthCheck } from '@/api/health';
import { Badge } from 'react-bootstrap';

export default function StatsFooter() {
  const { data: health } = useHealthCheck();

  if (!health) return null;

  return (
    <footer
      className="border-top bg-body-tertiary d-flex align-items-center justify-content-between px-3"
      style={{ height: '32px', fontSize: '0.8rem' }}
    >
      <div className="d-flex align-items-center gap-3">
        <span className="text-muted">
          <i className="bi bi-server me-1"></i>
          {health.status === 'healthy' ? (
            <Badge bg="success" className="py-0">
              Connected
            </Badge>
          ) : (
            <Badge bg="danger" className="py-0">
              Disconnected
            </Badge>
          )}
        </span>
        {health.uptime && (
          <span className="text-muted">
            <i className="bi bi-clock me-1"></i>
            Uptime: {health.uptime}
          </span>
        )}
      </div>
      <div className="text-muted">
        {health.version && (
          <span>
            <i className="bi bi-info-circle me-1"></i>v{health.version}
          </span>
        )}
      </div>
    </footer>
  );
}
