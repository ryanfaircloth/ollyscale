import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';
import StatsFooter from './StatsFooter';

export default function AppLayout() {
  return (
    <div className="d-flex vh-100">
      <Sidebar />
      <div className="flex-grow-1 d-flex flex-column overflow-hidden">
        <Header />
        <main className="flex-grow-1 overflow-auto">
          <Outlet />
        </main>
        <StatsFooter />
      </div>
    </div>
  );
}
