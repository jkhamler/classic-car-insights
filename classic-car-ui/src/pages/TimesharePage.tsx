import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Trash2, Car, Users } from 'lucide-react';
import clsx from 'clsx';
import {
  fetchSharedVehicles, createSharedVehicle,
  fetchCoOwners, createCoOwner,
  fetchVehicleOwners, linkOwnerToVehicle,
  fetchBookings, createBooking, deleteBooking,
  fetchExpenses, createExpense, deleteExpense,
  fetchVehicleBalance,
} from '../services/api';
import type { Expense } from '../types';

function BalanceBadge({ amount, currency }: { amount: number; currency: string }) {
  const color = amount >= 0 ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800';
  const label = amount >= 0 ? 'owed' : 'owes';
  return (
    <span className={clsx('inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold', color)}>
      {label} {currency} {Math.abs(amount).toFixed(2)}
    </span>
  );
}

function SetupForm() {
  const queryClient = useQueryClient();
  const [name, setName] = useState('DB9');
  const [make, setMake] = useState('Aston Martin');
  const [model, setModel] = useState('DB9');
  const [year, setYear] = useState('');
  const [ownerNames, setOwnerNames] = useState(['', '']);

  const setupMutation = useMutation({
    mutationFn: async () => {
      const vehicle = await createSharedVehicle({ name, make, model, year: year ? Number(year) : undefined });
      for (const ownerName of ownerNames) {
        if (!ownerName.trim()) continue;
        const owner = await createCoOwner({ name: ownerName.trim() });
        await linkOwnerToVehicle(vehicle.id, owner.id);
      }
      return vehicle;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['timeshare-vehicles'] });
    },
  });

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">Set up a shared vehicle</h2>
      <p className="mt-1 text-sm text-slate-500">One-time setup: add the car and the two co-owners.</p>

      <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-500">Name</label>
          <input value={name} onChange={(e) => setName(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-1.5 text-sm focus:border-emerald-500 focus:outline-none" />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-500">Year</label>
          <input type="number" value={year} onChange={(e) => setYear(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-1.5 text-sm focus:border-emerald-500 focus:outline-none" />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-500">Make</label>
          <input value={make} onChange={(e) => setMake(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-1.5 text-sm focus:border-emerald-500 focus:outline-none" />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-500">Model</label>
          <input value={model} onChange={(e) => setModel(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-1.5 text-sm focus:border-emerald-500 focus:outline-none" />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-500">Co-owner 1</label>
          <input value={ownerNames[0]} onChange={(e) => setOwnerNames([e.target.value, ownerNames[1]])}
            placeholder="e.g. Jonathan"
            className="w-full rounded-lg border border-slate-300 px-3 py-1.5 text-sm focus:border-emerald-500 focus:outline-none" />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-500">Co-owner 2</label>
          <input value={ownerNames[1]} onChange={(e) => setOwnerNames([ownerNames[0], e.target.value])}
            placeholder="e.g. Terry"
            className="w-full rounded-lg border border-slate-300 px-3 py-1.5 text-sm focus:border-emerald-500 focus:outline-none" />
        </div>
      </div>

      <button
        onClick={() => setupMutation.mutate()}
        disabled={!name.trim() || setupMutation.isPending}
        className="mt-4 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-50"
      >
        {setupMutation.isPending ? 'Setting up...' : 'Create'}
      </button>
      {setupMutation.isError && (
        <p className="mt-2 text-sm text-red-600">{(setupMutation.error as Error).message}</p>
      )}
    </div>
  );
}

function BookingsSection({ vehicleId }: { vehicleId: number }) {
  const queryClient = useQueryClient();
  const { data: owners } = useQuery({ queryKey: ['timeshare-owners', vehicleId], queryFn: () => fetchVehicleOwners(vehicleId) });
  const { data: coOwners } = useQuery({ queryKey: ['timeshare-co-owners'], queryFn: fetchCoOwners });
  const { data: bookings, isLoading } = useQuery({ queryKey: ['timeshare-bookings', vehicleId], queryFn: () => fetchBookings(vehicleId) });

  const ownerOptions = (owners ?? [])
    .map((o) => coOwners?.find((c) => c.id === o.co_owner_id))
    .filter((c): c is NonNullable<typeof c> => !!c);

  const [coOwnerId, setCoOwnerId] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [notes, setNotes] = useState('');

  const createMutation = useMutation({
    mutationFn: () => createBooking(vehicleId, { co_owner_id: Number(coOwnerId), start_date: startDate, end_date: endDate, notes: notes || null }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['timeshare-bookings', vehicleId] });
      setStartDate(''); setEndDate(''); setNotes('');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteBooking,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['timeshare-bookings', vehicleId] }),
  });

  return (
    <div className="space-y-3">
      <h2 className="text-lg font-semibold text-slate-900">Bookings</h2>

      <div className="flex flex-wrap items-end gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-500">Co-owner</label>
          <select value={coOwnerId} onChange={(e) => setCoOwnerId(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm focus:border-emerald-500 focus:outline-none">
            <option value="">Select...</option>
            {ownerOptions.map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-500">Start</label>
          <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm focus:border-emerald-500 focus:outline-none" />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-500">End</label>
          <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm focus:border-emerald-500 focus:outline-none" />
        </div>
        <div className="flex-1 min-w-[160px]">
          <label className="mb-1 block text-xs font-medium text-slate-500">Notes</label>
          <input value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Trip to the coast..."
            className="w-full rounded-lg border border-slate-300 px-3 py-1.5 text-sm focus:border-emerald-500 focus:outline-none" />
        </div>
        <button
          onClick={() => createMutation.mutate()}
          disabled={!coOwnerId || !startDate || !endDate || createMutation.isPending}
          className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-50"
        >Book</button>
      </div>
      {createMutation.isError && (
        <p className="text-sm text-red-600">{(createMutation.error as Error).message}</p>
      )}

      {isLoading ? (
        <p className="text-sm text-slate-500">Loading...</p>
      ) : !bookings?.length ? (
        <div className="rounded-xl border border-slate-200 bg-white p-8 text-center shadow-sm">
          <p className="text-sm text-slate-500">No bookings yet.</p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
          <table className="w-full min-w-[480px] text-sm">
            <thead className="border-b border-slate-200 bg-slate-50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-slate-500">Co-owner</th>
                <th className="px-4 py-3 text-left font-medium text-slate-500">Start</th>
                <th className="px-4 py-3 text-left font-medium text-slate-500">End</th>
                <th className="px-4 py-3 text-left font-medium text-slate-500">Notes</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {bookings.map((b) => (
                <tr key={b.id} className="hover:bg-slate-50">
                  <td className="px-4 py-3 font-medium text-slate-900">
                    {coOwners?.find((c) => c.id === b.co_owner_id)?.name ?? '—'}
                  </td>
                  <td className="px-4 py-3 text-slate-500">{b.start_date}</td>
                  <td className="px-4 py-3 text-slate-500">{b.end_date}</td>
                  <td className="px-4 py-3 text-slate-500">{b.notes ?? '—'}</td>
                  <td className="px-4 py-3">
                    <button onClick={() => deleteMutation.mutate(b.id)}
                      className="rounded-lg p-2 text-slate-400 hover:bg-red-50 hover:text-red-600">
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function ExpensesSection({ vehicleId }: { vehicleId: number }) {
  const queryClient = useQueryClient();
  const { data: owners } = useQuery({ queryKey: ['timeshare-owners', vehicleId], queryFn: () => fetchVehicleOwners(vehicleId) });
  const { data: coOwners } = useQuery({ queryKey: ['timeshare-co-owners'], queryFn: fetchCoOwners });
  const { data: expenses, isLoading } = useQuery({ queryKey: ['timeshare-expenses', vehicleId], queryFn: () => fetchExpenses(vehicleId) });

  const ownerOptions = (owners ?? [])
    .map((o) => coOwners?.find((c) => c.id === o.co_owner_id))
    .filter((c): c is NonNullable<typeof c> => !!c);

  const [coOwnerId, setCoOwnerId] = useState('');
  const [contributionType, setContributionType] = useState<Expense['contribution_type']>('cash');
  const [category, setCategory] = useState<Expense['category']>('other');
  const [amount, setAmount] = useState('');
  const [expenseDate, setExpenseDate] = useState('');
  const [description, setDescription] = useState('');

  const createMutation = useMutation({
    mutationFn: () => createExpense(vehicleId, {
      co_owner_id: Number(coOwnerId),
      contribution_type: contributionType,
      category,
      amount: Number(amount),
      expense_date: expenseDate,
      description: description || null,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['timeshare-expenses', vehicleId] });
      queryClient.invalidateQueries({ queryKey: ['timeshare-balance', vehicleId] });
      setAmount(''); setExpenseDate(''); setDescription('');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteExpense,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['timeshare-expenses', vehicleId] });
      queryClient.invalidateQueries({ queryKey: ['timeshare-balance', vehicleId] });
    },
  });

  return (
    <div className="space-y-3">
      <h2 className="text-lg font-semibold text-slate-900">Expenses</h2>

      <div className="flex flex-wrap items-end gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-500">Co-owner</label>
          <select value={coOwnerId} onChange={(e) => setCoOwnerId(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm focus:border-emerald-500 focus:outline-none">
            <option value="">Select...</option>
            {ownerOptions.map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-500">Type</label>
          <select value={contributionType} onChange={(e) => setContributionType(e.target.value as Expense['contribution_type'])}
            className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm focus:border-emerald-500 focus:outline-none">
            <option value="cash">Cash</option>
            <option value="labour">Labour</option>
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-500">Category</label>
          <select value={category} onChange={(e) => setCategory(e.target.value as Expense['category'])}
            className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm focus:border-emerald-500 focus:outline-none">
            <option value="insurance">Insurance</option>
            <option value="servicing">Servicing</option>
            <option value="fuel">Fuel</option>
            <option value="other">Other</option>
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-500">Amount (£)</label>
          <input type="number" value={amount} onChange={(e) => setAmount(e.target.value)}
            className="w-24 rounded-lg border border-slate-300 px-3 py-1.5 text-sm focus:border-emerald-500 focus:outline-none" />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-500">Date</label>
          <input type="date" value={expenseDate} onChange={(e) => setExpenseDate(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm focus:border-emerald-500 focus:outline-none" />
        </div>
        <div className="flex-1 min-w-[160px]">
          <label className="mb-1 block text-xs font-medium text-slate-500">Description</label>
          <input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Annual premium..."
            className="w-full rounded-lg border border-slate-300 px-3 py-1.5 text-sm focus:border-emerald-500 focus:outline-none" />
        </div>
        <button
          onClick={() => createMutation.mutate()}
          disabled={!coOwnerId || !amount || !expenseDate || createMutation.isPending}
          className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-50"
        >Add</button>
      </div>
      {createMutation.isError && (
        <p className="text-sm text-red-600">{(createMutation.error as Error).message}</p>
      )}

      {isLoading ? (
        <p className="text-sm text-slate-500">Loading...</p>
      ) : !expenses?.length ? (
        <div className="rounded-xl border border-slate-200 bg-white p-8 text-center shadow-sm">
          <p className="text-sm text-slate-500">No expenses logged yet.</p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
          <table className="w-full min-w-[640px] text-sm">
            <thead className="border-b border-slate-200 bg-slate-50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-slate-500">Date</th>
                <th className="px-4 py-3 text-left font-medium text-slate-500">Co-owner</th>
                <th className="px-4 py-3 text-left font-medium text-slate-500">Type</th>
                <th className="px-4 py-3 text-left font-medium text-slate-500">Category</th>
                <th className="px-4 py-3 text-left font-medium text-slate-500">Amount</th>
                <th className="px-4 py-3 text-left font-medium text-slate-500">Description</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {expenses.map((e) => (
                <tr key={e.id} className="hover:bg-slate-50">
                  <td className="px-4 py-3 text-slate-500">{e.expense_date}</td>
                  <td className="px-4 py-3 font-medium text-slate-900">
                    {coOwners?.find((c) => c.id === e.co_owner_id)?.name ?? '—'}
                  </td>
                  <td className="px-4 py-3">
                    <span className="rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-600">{e.contribution_type}</span>
                  </td>
                  <td className="px-4 py-3 text-slate-500">{e.category}</td>
                  <td className="px-4 py-3 font-semibold">{e.currency} {e.amount.toFixed(2)}</td>
                  <td className="px-4 py-3 text-slate-500">{e.description ?? '—'}</td>
                  <td className="px-4 py-3">
                    <button onClick={() => deleteMutation.mutate(e.id)}
                      className="rounded-lg p-2 text-slate-400 hover:bg-red-50 hover:text-red-600">
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function BalanceSection({ vehicleId }: { vehicleId: number }) {
  const { data: balance, isLoading } = useQuery({ queryKey: ['timeshare-balance', vehicleId], queryFn: () => fetchVehicleBalance(vehicleId) });

  if (isLoading || !balance?.entries.length) return null;
  const { currency } = balance;

  return (
    <div className="space-y-3">
      <h2 className="text-lg font-semibold text-slate-900">Balance</h2>

      {balance.settlements.length > 0 && (
        <div className="space-y-2">
          {balance.settlements.map((s, i) => (
            <div key={i} className="flex items-center justify-between rounded-xl border border-amber-200 bg-amber-50 px-4 py-3">
              <p className="text-sm font-semibold text-amber-900">
                {s.from_name} owes {s.to_name}
              </p>
              <p className="text-sm font-bold text-amber-900">{currency} {s.amount.toFixed(2)}</p>
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-medium text-slate-500">Total spend</p>
          <p className="mt-1 text-xl font-bold text-slate-900">{currency} {balance.total_spend.toFixed(2)}</p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-medium text-slate-500">Cash contributed</p>
          <p className="mt-1 text-xl font-bold text-slate-900">{currency} {balance.total_cash.toFixed(2)}</p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-medium text-slate-500">Labour contributed</p>
          <p className="mt-1 text-xl font-bold text-slate-900">{currency} {balance.total_labour.toFixed(2)}</p>
        </div>
      </div>

      {balance.by_category.length > 0 && (
        <div className="flex flex-wrap gap-2 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          {balance.by_category.map((c) => (
            <span key={c.category} className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
              {c.category}: {currency} {c.amount.toFixed(2)}
            </span>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {balance.entries.map((entry) => (
          <div key={entry.co_owner_id} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="flex items-center justify-between">
              <p className="text-sm font-semibold text-slate-900">{entry.name}</p>
              <BalanceBadge amount={entry.net_balance} currency={currency} />
            </div>
            <p className="mt-2 text-xs text-slate-500">
              Contributed {currency} {entry.total_contributed.toFixed(2)} ({currency} {entry.cash_contributed.toFixed(2)} cash · {currency} {entry.labour_contributed.toFixed(2)} labour) · fair share {currency} {entry.fair_share.toFixed(2)}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function TimesharePage() {
  const { data: vehicles, isLoading } = useQuery({ queryKey: ['timeshare-vehicles'], queryFn: fetchSharedVehicles });
  const vehicle = vehicles?.[0];

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Users className="h-6 w-6 text-slate-400" />
        <h1 className="text-2xl font-bold text-slate-900">Timeshare</h1>
      </div>

      {isLoading ? (
        <p className="text-sm text-slate-500">Loading...</p>
      ) : !vehicle ? (
        <SetupForm />
      ) : (
        <>
          <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <Car className="h-5 w-5 text-slate-400" />
            <p className="text-sm font-semibold text-slate-900">
              {vehicle.name} {vehicle.make && `· ${vehicle.make} ${vehicle.model ?? ''}`} {vehicle.year && `(${vehicle.year})`}
            </p>
          </div>
          <BalanceSection vehicleId={vehicle.id} />
          <BookingsSection vehicleId={vehicle.id} />
          <ExpensesSection vehicleId={vehicle.id} />
        </>
      )}
    </div>
  );
}
