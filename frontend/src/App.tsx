import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import AppLayout from './components/Layout';
import DashboardPage from './pages/DashboardPage';
import ProductsPage from './pages/ProductsPage';
import UploadPage from './pages/UploadPage';
import CostsPage from './pages/CostsPage';
import AdsPage from './pages/AdsPage';
import EventsPage from './pages/EventsPage';
import ReportsPage from './pages/ReportsPage';
import AnalysisPage from './pages/AnalysisPage';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem('token');
  if (!token) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
          <Route index element={<DashboardPage />} />
          <Route path="products" element={<ProductsPage />} />
          <Route path="upload" element={<UploadPage />} />
          <Route path="costs" element={<CostsPage />} />
          <Route path="ads" element={<AdsPage />} />
          <Route path="events" element={<EventsPage />} />
          <Route path="reports" element={<ReportsPage />} />
          <Route path="analysis" element={<AnalysisPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
