import { useEffect, useState } from 'react';
import { Card, Col, Row, Statistic, Table, Typography, Spin } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import api from '../api/client';
import type { ProfitByProduct } from '../types';

const { Title } = Typography;

export default function DashboardPage() {
  const [products, setProducts] = useState<ProfitByProduct[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const now = new Date();
        const start = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-01`;
        const end = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate()).padStart(2, '0')}`;
        const resp = await api.get(`/reports/profit/all?period_start=${start}&period_end=${end}`);
        setProducts(resp.data);
      } catch {
        setProducts([]);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const totalRevenue = products.reduce((sum, p) => sum + p.total_revenue, 0);
  const totalProfit = products.reduce((sum, p) => sum + p.total_net_profit, 0);
  const avgRate = totalRevenue > 0 ? (totalProfit / totalRevenue * 100) : 0;

  const columns = [
    { title: '상품명', dataIndex: 'product_name', key: 'product_name' },
    { title: 'SKU', dataIndex: 'sku', key: 'sku' },
    { title: '총 매출', dataIndex: 'total_revenue', key: 'total_revenue',
      render: (v: number) => `₩${v.toLocaleString()}` },
    { title: '순이익', dataIndex: 'total_net_profit', key: 'total_net_profit',
      render: (v: number) => <span style={{ color: v >= 0 ? '#3f8600' : '#cf1322' }}>₩{v.toLocaleString()}</span> },
    { title: '수익률', dataIndex: 'total_profit_rate', key: 'total_profit_rate',
      render: (v: number) => <span style={{ color: v >= 0 ? '#3f8600' : '#cf1322' }}>{v.toFixed(1)}%</span> },
  ];

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;

  return (
    <>
      <Title level={4}>이번 달 수익 요약</Title>
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card><Statistic title="총 매출" value={totalRevenue} prefix="₩" /></Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic title="총 순이익" value={totalProfit} prefix="₩"
              valueStyle={{ color: totalProfit >= 0 ? '#3f8600' : '#cf1322' }}
              suffix={totalProfit >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />} />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic title="평균 수익률" value={avgRate} precision={1} suffix="%"
              valueStyle={{ color: avgRate >= 0 ? '#3f8600' : '#cf1322' }} />
          </Card>
        </Col>
      </Row>
      <Table dataSource={products} columns={columns} rowKey="product_id" pagination={false} />
    </>
  );
}
