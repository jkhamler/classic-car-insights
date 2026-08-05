import { Outlet } from 'react-router-dom';
import Sidebar from './components/layout/Sidebar';

export default function App() {
  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar />
      <main className="p-4 sm:p-6 md:ml-56">
        <Outlet />
      </main>
    </div>
  );
}
