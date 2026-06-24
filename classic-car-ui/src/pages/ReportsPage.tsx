import { useQuery } from '@tanstack/react-query';
import { FileText } from 'lucide-react';
import { fetchWeeklyDigest } from '../services/api';

export default function ReportsPage() {
  const { data: digest, isLoading } = useQuery({ queryKey: ['weekly-digest'], queryFn: fetchWeeklyDigest });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-900">Reports</h1>

      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold text-slate-900">
          <FileText className="h-5 w-5" /> Weekly Market Digest
        </h2>

        {isLoading ? (
          <p className="text-sm text-slate-500">Loading...</p>
        ) : !digest ? (
          <p className="text-sm text-slate-500">
            No weekly digest generated yet. The AI digest is generated automatically on Monday mornings,
            or can be triggered via the admin API.
          </p>
        ) : (
          <div>
            <p className="mb-4 text-xs text-slate-400">
              Generated: {new Date(digest.generated_at).toLocaleString()}
            </p>
            <div className="prose prose-sm max-w-none text-slate-700"
                 dangerouslySetInnerHTML={{ __html: digest.content.replace(/\n/g, '<br/>') }} />
          </div>
        )}
      </div>
    </div>
  );
}
