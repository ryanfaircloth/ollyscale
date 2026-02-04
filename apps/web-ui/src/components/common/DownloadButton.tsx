import { Button } from 'react-bootstrap';

interface DownloadButtonProps {
  data: unknown;
  filename: string;
  size?: 'sm' | 'lg';
  variant?: string;
  className?: string;
}

export function DownloadButton({
  data,
  filename,
  size = 'sm',
  variant = 'outline-secondary',
  className = '',
}: DownloadButtonProps) {
  const handleDownload = () => {
    try {
      const jsonStr = JSON.stringify(data, null, 2);
      const blob = new Blob([jsonStr], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to download:', err);
    }
  };

  return (
    <Button variant={variant} size={size} onClick={handleDownload} className={className}>
      <i className="bi bi-download me-1"></i>
      Download JSON
    </Button>
  );
}
