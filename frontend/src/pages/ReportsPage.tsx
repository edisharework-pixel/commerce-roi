import { useEffect, useState } from 'react';
import {
  Table, Select, DatePicker, Card, Space, Typography, Descriptions, Spin,
} from 'antd';
import api from '../api/client';
import PlatformCompare from '../components/PlatformCompare';
import type { Product, ProfitByProduct, PlatformProfit } from '../types';

const { Title } = Typography;
const { RangePicker } = DatePicker;

export default function ReportsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [selectedProduct, setSelectedProduct] = useState<number | undefined>();
  const [dateRange, setDateRange] = useState<[string, string] | null>(null);
  const [granularity, setGranularity] = useState<string>('month');

  const [profitData, setProfitData] = useState<ProfitByProduct[]>([]);
  const [loading, setLoading] = useState(false);
  const [unmatchedSummary, setUnmatchedSummary] = useState<{ unmatched_sales: number; unmatched_ads: number } | null>(null);

  /* 플랫폼 비교용 */
  const [selectedPlatforms, setSelectedPlatforms] = useState<PlatformProfit[]>([]);

  useEffect(() => {
    api.get('/products').then(r => setProducts(r.data));
  }, []);

  const fetchReport = async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = { granularity };
      if (selectedProduct) params.product_id = String(selectedProduct);
      if (dateRange) { params.start_date = dateRange[0]; params.end_date = dateRange[1]; }
      const resp = await api.get('/reports/profit', { params });
      const data: ProfitByProduct[] = resp.data;
      setProfitData(data);

      // 선택된 상품의 플랫폼 데이터
      if (selectedProduct) {
        const found = data.find(d => d.product_id === selectedProduct);
        setSelectedPlatforms(found?.platforms ?? []);
      } else if (data.length > 0) {
        setSelectedPlatforms(data[0].platforms);
      } else {
        setSelectedPlatforms([]);
      }
    } finally { setLoading(false); }
  };

  const fetchUnmatched = async () => {
    try {
      const [sales, ads] = await Promise.all([
        api.get('/upload/unmatched').catch(() => ({ data: [] })),
        api.get('/ads/unmatched').catch(() => ({ data: [] })),
      ]);
      setUnmatchedSummary({
        unmatched_sales: Array.isArray(sales.data) ? sales.data.length : 0,
        unmatched_ads: Array.isArray(ads.data) ? ads.data.length : 0,
      });
    } catch {
      setUnmatchedSummary(null);
    }
  };

  useEffect(() => { fetchReport(); fetchUnmatched(); }, [selectedProduct, dateRange, granularity]);

  const profitColumns = [
    { title: '상품', dataIndex: 'product_name' },
    { title: 'SKU', dataIndex: 'sku' },
    { title: '총 매출', dataIndex: 'total_revenue', render: (v: number) => `₩${Number(v).toLocaleString()}` },
    { title: '총 순이익', dataIndex: 'total_net_profit', render: (v: number) => `₩${Number(v).toLocaleString()}` },
    { title: '이익률', dataIndex: 'total_profit_rate', render: (v: number) => `${(Number(v) * 100).toFixed(1)}%` },
  ];

  const platformColumns = [
    { title: '플랫폼', dataIndex: 'platform_name' },
    { title: '매출', dataIndex: 'revenue', render: (v: number) => `₩${Number(v).toLocaleString()}` },
    { title: '원가', dataIndex: 'cost_of_goods', render: (v: number) => `₩${Number(v).toLocaleString()}` },
    { title: '수수료', dataIndex: 'platform_fee', render: (v: number) => `₩${Number(v).toLocaleString()}` },
    { title: '광고비', dataIndex: 'ad_cost', render: (v: number) => `₩${Number(v).toLocaleString()}` },
    { title: '순이익', dataIndex: 'net_profit', render: (v: number) => `₩${Number(v).toLocaleString()}` },
    { title: '이익률', dataIndex: 'profit_rate', render: (v: number) => `${(Number(v) * 100).toFixed(1)}%` },
  ];

  return (
    <>
      <Title level={4} style={{ marginBottom: 16 }}>수익 리포트</Title>

      {/* 필터 */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Space wrap>
          <Select allowClear placeholder="상품 선택" style={{ width: 220 }} showSearch optionFilterProp="label"
            options={products.map(p => ({ value: p.id, label: p.name }))}
            onChange={v => setSelectedProduct(v)} />
          <RangePicker onChange={(_, ds) => ds[0] ? setDateRange([ds[0], ds[1]]) : setDateRange(null)} />
          <Select value={granularity} style={{ width: 100 }} onChange={v => setGranularity(v)}
            options={[
              { value: 'day', label: '일' },
              { value: 'week', label: '주' },
              { value: 'month', label: '월' },
            ]} />
        </Space>
      </Card>

      <Spin spinning={loading}>
        {/* 수익 요약 테이블 */}
        <Card title="수익 요약" size="small" style={{ marginBottom: 16 }}>
          <Table
            dataSource={profitData}
            columns={profitColumns}
            rowKey="product_id"
            pagination={false}
            expandable={{
              expandedRowRender: (record: ProfitByProduct) => (
                <Table
                  dataSource={record.platforms}
                  columns={platformColumns}
                  rowKey="platform_id"
                  pagination={false}
                  size="small"
                />
              ),
            }}
            onRow={(record: ProfitByProduct) => ({
              onClick: () => setSelectedPlatforms(record.platforms),
              style: { cursor: 'pointer' },
            })}
          />
        </Card>

        {/* 플랫폼 비교 차트 */}
        <Card title="플랫폼 비교" size="small" style={{ marginBottom: 16 }}>
          {selectedPlatforms.length > 0 ? (
            <PlatformCompare data={selectedPlatforms} />
          ) : (
            <div style={{ textAlign: 'center', padding: 40, color: '#999' }}>상품을 선택하면 플랫폼 비교 차트가 표시됩니다.</div>
          )}
        </Card>

        {/* 미매칭 현황 */}
        <Card title="미매칭 현황" size="small">
          {unmatchedSummary ? (
            <Descriptions column={2}>
              <Descriptions.Item label="미매칭 판매건">{unmatchedSummary.unmatched_sales}건</Descriptions.Item>
              <Descriptions.Item label="미매칭 광고건">{unmatchedSummary.unmatched_ads}건</Descriptions.Item>
            </Descriptions>
          ) : (
            <div style={{ color: '#999' }}>데이터를 불러올 수 없습니다.</div>
          )}
        </Card>
      </Spin>
    </>
  );
}
