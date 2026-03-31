import { useState } from 'react';
import { Form, Input, Button, Card, message, Typography } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useAuth } from '../hooks/useAuth';
import { useNavigate } from 'react-router-dom';

const { Title } = Typography;

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  const onFinish = async (values: { username: string; password: string }) => {
    setLoading(true);
    try {
      await login(values.username, values.password);
      message.success('로그인 성공');
      navigate('/');
    } catch {
      message.error('로그인 실패: 아이디 또는 비밀번호를 확인하세요');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', background: '#f0f2f5' }}>
      <Card style={{ width: 400 }}>
        <Title level={3} style={{ textAlign: 'center', marginBottom: 24 }}>Commerce ROI</Title>
        <Form onFinish={onFinish} size="large">
          <Form.Item name="username" rules={[{ required: true, message: '아이디를 입력하세요' }]}>
            <Input prefix={<UserOutlined />} placeholder="아이디" />
          </Form.Item>
          <Form.Item name="password" rules={[{ required: true, message: '비밀번호를 입력하세요' }]}>
            <Input.Password prefix={<LockOutlined />} placeholder="비밀번호" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block>로그인</Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
