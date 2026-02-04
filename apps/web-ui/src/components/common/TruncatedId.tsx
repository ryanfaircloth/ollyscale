import { OverlayTrigger, Tooltip } from 'react-bootstrap';
import { CopyButton } from './CopyButton';

interface TruncatedIdProps {
  id: string;
  maxLength?: number;
  showCopy?: boolean;
}

/**
 * Display a truncated ID (trace_id, span_id, etc.) with ellipsis indicator,
 * tooltip showing full ID on hover, and optional copy button
 */
export function TruncatedId({ id, maxLength = 8, showCopy = true }: TruncatedIdProps) {
  if (!id) return <span className="text-muted">-</span>;

  const truncated = id.length > maxLength ? id.substring(0, maxLength) + '...' : id;
  const isTruncated = id.length > maxLength;

  const idDisplay = (
    <code className="small" style={{ cursor: isTruncated ? 'help' : 'default' }}>
      {truncated}
    </code>
  );

  const content = (
    <span className="d-inline-flex align-items-center gap-1">
      {isTruncated ? (
        <OverlayTrigger
          placement="top"
          overlay={
            <Tooltip>
              <code className="text-white">{id}</code>
            </Tooltip>
          }
        >
          {idDisplay}
        </OverlayTrigger>
      ) : (
        idDisplay
      )}
      {showCopy && <CopyButton text={id} size="sm" variant="link" className="p-0 ms-1" />}
    </span>
  );

  return content;
}
