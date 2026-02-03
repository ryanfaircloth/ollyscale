import { useNavigate } from 'react-router-dom';
import { TruncatedId } from './TruncatedId';

interface NavigableSpanIdProps {
  spanId: string;
  traceId: string;
  maxLength?: number;
  showCopy?: boolean;
  className?: string;
}

/**
 * Displays a span ID that navigates to the traces page and opens the specific span when clicked
 */
export function NavigableSpanId({
  spanId,
  traceId,
  maxLength = 12,
  showCopy = true,
  className = '',
}: NavigableSpanIdProps) {
  const navigate = useNavigate();

  const handleClick = () => {
    // Navigate to traces page with trace_id filter and specific span_id to open
    navigate('/traces', {
      state: {
        filterTraceId: traceId,
        openSpanId: spanId,
      },
    });
  };

  return (
    <span
      onClick={handleClick}
      className={`cursor-pointer text-primary text-decoration-underline ${className}`}
      style={{ cursor: 'pointer' }}
      title="Click to view span details"
    >
      <TruncatedId id={spanId} maxLength={maxLength} showCopy={showCopy} />
    </span>
  );
}
