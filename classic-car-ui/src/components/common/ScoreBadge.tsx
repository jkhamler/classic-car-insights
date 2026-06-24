import clsx from 'clsx';

export default function ScoreBadge({ score }: { score: number | null }) {
  if (score === null || score === undefined) return null;

  const color =
    score >= 70
      ? 'bg-emerald-100 text-emerald-800'
      : score >= 40
        ? 'bg-amber-100 text-amber-800'
        : 'bg-red-100 text-red-800';

  return (
    <span className={clsx('inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold', color)}>
      {score.toFixed(0)}
    </span>
  );
}
