import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import AppLayout from './components/Layout';
import DashboardPage from './pages/DashboardPage';

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
          <Route path="products" element={<div>상품 관리 (준비중)</div>} />
          <Route path="upload" element={<div>업로드 (준비중)</div>} />
          <Route path="costs" element={<div>비용 관리 (준비중)</div>} />
          <Route path="ads" element={<div>광고 분석 (준비중)</div>} />
          <Route path="events" element={<div>변경 이벤트 (준비중)</div>} />
          <Route path="reports" element={<div>수익 리포트 (준비중)</div>} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
