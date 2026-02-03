import { useNavigate } from 'react-router-dom';
import { TruncatedId } from './TruncatedId';

interface NavigableTraceIdProps {
  traceId: string;
  maxLength?: number;
  showCopy?: boolean;
  className?: string;
}

/**
 * Displays a trace ID that navigates to the traces page with filters when clicked
 */
export function NavigableTraceId({ traceId, maxLength = 16, showCopy = true, className = '' }: NavigableTraceIdProps) {
  const navigate = useNavigate();

  const handleClick = () => {
    // Navigate to traces page with trace_id filter
    navigate('/traces', {
      state: {
        filterTraceId: traceId,
      },
    });
  };

  return (
    <span
      onClick={handleClick}
      className={`cursor-pointer text-primary text-decoration-underline ${className}`}
      style={{ cursor: 'pointer' }}
      title="Click to view trace details"
    >
      <TruncatedId id={traceId} maxLength={maxLength} showCopy={showCopy} />
    </span>
  );
}
