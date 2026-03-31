import { useEffect, useState } from 'react';
import { Card, Select, DatePicker, Button, Table, Typography, Spin, message } from 'antd';
import { RobotOutlined } from '@ant-design/icons';
import api from '../api/client';
import type { Product } from '../types';

const { Title, Paragraph } = Typography;
const { RangePicker } = DatePicker;

interface AnalysisResult {
  analysis_result: { platforms?: Array<Record<string, number | string>> };
  suggestions: string;
  log_id?: number;
}

export default function AnalysisPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [selectedProduct, setSelectedProduct] = useState<number | null>(null);
  const [dates, setDates] = useState<[any, any] | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);

  useEffect(() => {
    api.get('/products').then(r => setProducts(r.data));
  }, []);

  const runAnalysis = async () => {
    if (!selectedProduct || !dates) {
      message.warning('상품과 기간을 선택하세요');
      return;
    }
    setLoading(true);
    try {
      const resp = await api.post(`/analysis/ads?product_id=${selectedProduct}&period_start=${dates[0].format('YYYY-MM-DD')}&period_end=${dates[1].format('YYYY-MM-DD')}`);
      setResult(resp.data);
      message.success('분석 완료');
    } catch {
      message.error('분석 실패');
    } finally {
      setLoading(false);
    }
  };

  const metricColumns = [
    { title: '플랫폼', dataIndex: 'platform', key: 'platform' },
    { title: '광고비', dataIndex: 'spend', key: 'spend', render: (v: number) => `₩${v?.toLocaleString()}` },
    { title: 'ROAS', dataIndex: 'roas', key: 'roas' },
    { title: 'CPC', dataIndex: 'cpc', key: 'cpc', render: (v: number) => `₩${v?.toLocaleString()}` },
    { title: 'CTR', dataIndex: 'ctr', key: 'ctr', render: (v: number) => `${v}%` },
    { title: '전환율', dataIndex: 'cvr', key: 'cvr', render: (v: number) => `${v}%` },
    { title: '전환수', dataIndex: 'conversions', key: 'conversions' },
    { title: '매출', dataIndex: 'revenue', key: 'revenue', render: (v: number) => `₩${v?.toLocaleString()}` },
  ];

  return (
    <>
      <Title level={4}><RobotOutlined /> AI 광고 분석</Title>
      <Card style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', gap: 16, alignItems: 'end', flexWrap: 'wrap' }}>
          <div>
            <div style={{ marginBottom: 4 }}>상품</div>
            <Select style={{ width: 300 }} placeholder="상품 선택"
              options={products.map(p => ({ value: p.id, label: `${p.name} (${p.sku})` }))}
              onChange={setSelectedProduct} />
          </div>
          <div>
            <div style={{ marginBottom: 4 }}>기간</div>
            <RangePicker onChange={(d) => setDates(d as [any, any])} />
          </div>
          <Button type="primary" icon={<RobotOutlined />} onClick={runAnalysis} loading={loading}>
            AI 분석 실행
          </Button>
        </div>
      </Card>

      {loading && <Spin size="large" style={{ display: 'block', margin: '50px auto' }} />}

      {result && !loading && (
        <>
          {result.analysis_result.platforms && (
            <Card title="플랫폼별 광고 성과" style={{ marginBottom: 24 }}>
              <Table dataSource={result.analysis_result.platforms} columns={metricColumns}
                rowKey="platform" pagination={false} />
            </Card>
          )}
          <Card title="AI 개선 제안">
            <Paragraph style={{ whiteSpace: 'pre-wrap' }}>{result.suggestions}</Paragraph>
          </Card>
        </>
      )}
    </>
  );
}
