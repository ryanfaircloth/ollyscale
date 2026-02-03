import { Button } from 'react-bootstrap';

interface RefreshButtonProps {
  onRefresh: () => void;
  isRefreshing?: boolean;
  size?: 'sm' | 'lg';
  variant?: string;
  className?: string;
}

export function RefreshButton({
  onRefresh,
  isRefreshing = false,
  size = 'sm',
  variant = 'outline-primary',
  className = '',
}: RefreshButtonProps) {
  return (
    <Button
      variant={variant}
      size={size}
      onClick={onRefresh}
      disabled={isRefreshing}
      className={className}
    >
      <i className={`bi bi-arrow-clockwise me-1 ${isRefreshing ? 'spin' : ''}`}></i>
      {isRefreshing ? 'Refreshing...' : 'Refresh'}
    </Button>
  );
}
