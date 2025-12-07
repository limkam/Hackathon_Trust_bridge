import { useRouter } from 'next/router';
import { ArrowLeft } from 'lucide-react';

export default function BackButton({ label = 'Back', href = null, className = '' }) {
  const router = useRouter();

  const handleClick = () => {
    if (href) {
      router.push(href);
    } else {
      router.back();
    }
  };

  return (
    <button
      onClick={handleClick}
      className={`flex items-center gap-2 text-gray-700 hover:text-trust-blue transition-colors ${className}`}
    >
      <ArrowLeft className="w-4 h-4" />
      <span>{label}</span>
    </button>
  );
}

