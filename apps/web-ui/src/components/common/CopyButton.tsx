import { useState } from 'react';
import { Button } from 'react-bootstrap';

interface CopyButtonProps {
  text: string;
  size?: 'sm' | 'lg';
  variant?: string;
  className?: string;
}

export function CopyButton({ text, size = 'sm', variant = 'outline-secondary', className = '' }: CopyButtonProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  return (
    <Button
      variant={copied ? 'success' : variant}
      size={size}
      onClick={handleCopy}
      className={className}
    >
      <i className={`bi bi-${copied ? 'check' : 'clipboard'} me-1`}></i>
      {copied ? 'Copied!' : 'Copy'}
    </Button>
  );
}
