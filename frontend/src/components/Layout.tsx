import { Layout, Menu } from 'antd';
import {
  DashboardOutlined,
  ShoppingOutlined,
  UploadOutlined,
  DollarOutlined,
  FundOutlined,
  CalendarOutlined,
  BarChartOutlined,
  LogoutOutlined,
} from '@ant-design/icons';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';

const { Sider, Content, Header } = Layout;

const menuItems = [
  { key: '/', icon: <DashboardOutlined />, label: '대시보드' },
  { key: '/products', icon: <ShoppingOutlined />, label: '상품 관리' },
  { key: '/upload', icon: <UploadOutlined />, label: '데이터 업로드' },
  { key: '/costs', icon: <DollarOutlined />, label: '비용 관리' },
  { key: '/ads', icon: <FundOutlined />, label: '광고 분석' },
  { key: '/events', icon: <CalendarOutlined />, label: '변경 이벤트' },
  { key: '/reports', icon: <BarChartOutlined />, label: '수익 리포트' },
];

export default function AppLayout() {
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible>
        <div style={{ height: 32, margin: 16, color: '#fff', fontSize: 18, fontWeight: 'bold', textAlign: 'center' }}>
          Commerce ROI
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={[
            ...menuItems,
            { key: 'logout', icon: <LogoutOutlined />, label: '로그아웃', danger: true },
          ]}
          onClick={({ key }) => key === 'logout' ? handleLogout() : navigate(key)}
        />
      </Sider>
      <Layout>
        <Header style={{ padding: '0 24px', background: '#fff', fontSize: 16, fontWeight: 600 }}>
          커머스 수익분석
        </Header>
        <Content style={{ margin: 24, padding: 24, background: '#fff', borderRadius: 8, minHeight: 280 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
