import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Trash2, Bell } from 'lucide-react';
import { fetchAlerts, deleteAlert } from '../services/api';

export default function AlertsPage() {
  const queryClient = useQueryClient();
  const { data: alerts, isLoading } = useQuery({ queryKey: ['alerts'], queryFn: fetchAlerts });

  const deleteMutation = useMutation({
    mutationFn: deleteAlert,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['alerts'] }),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">Alerts</h1>
      </div>

      {isLoading ? (
        <p className="text-sm text-slate-500">Loading...</p>
      ) : !alerts?.length ? (
        <div className="rounded-xl border border-slate-200 bg-white p-8 text-center shadow-sm">
          <Bell className="mx-auto h-10 w-10 text-slate-300" />
          <p className="mt-3 text-sm text-slate-500">No alerts configured yet.</p>
          <p className="text-xs text-slate-400">Alerts can be created via the API.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {alerts.map((alert) => (
            <div key={alert.id} className="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <div>
                <p className="text-sm font-semibold text-slate-900">{alert.name}</p>
                <p className="text-xs text-slate-500">
                  Type: {alert.alert_type} · Channel: {alert.notification_channel}
                  {alert.last_triggered_at && ` · Last triggered: ${new Date(alert.last_triggered_at).toLocaleDateString()}`}
                </p>
              </div>
              <button
                onClick={() => deleteMutation.mutate(alert.id)}
                className="rounded-lg p-2 text-slate-400 hover:bg-red-50 hover:text-red-600"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
