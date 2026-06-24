import { Outlet } from 'react-router-dom';
import Sidebar from './components/layout/Sidebar';

export default function App() {
  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar />
      <main className="ml-56 p-6">
        <Outlet />
      </main>
    </div>
  );
}
