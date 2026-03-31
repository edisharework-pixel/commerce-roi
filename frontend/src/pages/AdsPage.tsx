import { useEffect, useState } from 'react';
import {
  Table, Button, Modal, Form, Select, Input, Tag, Space, Typography, DatePicker, Popconfirm, message,
} from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import api from '../api/client';
import type { AdData, AdCampaignMapping, Platform, Product } from '../types';

const { Title } = Typography;
const { RangePicker } = DatePicker;

export default function AdsPage() {
  /* state — 광고 데이터 */
  const [ads, setAds] = useState<AdData[]>([]);
  const [adsLoading, setAdsLoading] = useState(true);
  const [platformFilter, setPlatformFilter] = useState<number | undefined>();
  const [dateRange, setDateRange] = useState<[string, string] | null>(null);

  /* state — 매핑 */
  const [mappings, setMappings] = useState<AdCampaignMapping[]>([]);
  const [mapLoading, setMapLoading] = useState(true);
  const [mapModalOpen, setMapModalOpen] = useState(false);
  const [mapForm] = Form.useForm();

  /* reference data */
  const [platforms, setPlatforms] = useState<Platform[]>([]);
  const [products, setProducts] = useState<Product[]>([]);

  const fetchAds = async () => {
    setAdsLoading(true);
    try {
      const params: Record<string, string> = {};
      if (platformFilter) params.platform_id = String(platformFilter);
      if (dateRange) { params.start_date = dateRange[0]; params.end_date = dateRange[1]; }
      setAds((await api.get('/ads', { params })).data);
    } finally { setAdsLoading(false); }
  };

  const fetchMappings = async () => {
    setMapLoading(true);
    try { setMappings((await api.get('/ads/campaign-mapping')).data); } finally { setMapLoading(false); }
  };

  useEffect(() => {
    api.get('/platforms').then(r => setPlatforms(r.data));
    api.get('/products').then(r => setProducts(r.data));
    fetchAds();
    fetchMappings();
  }, []);

  useEffect(() => { fetchAds(); }, [platformFilter, dateRange]);

  /* 매핑 생성 */
  const handleCreateMapping = async (values: { platform_id: number; campaign_name: string; product_id: number; allocation_method: string }) => {
    try {
      await api.post('/ads/campaign-mapping', values);
      message.success('매핑 추가 완료');
      setMapModalOpen(false);
      mapForm.resetFields();
      fetchMappings();
    } catch { message.error('매핑 추가 실패'); }
  };

  const handleDeleteMapping = async (id: number) => {
    try {
      await api.delete(`/ads/campaign-mapping/${id}`);
      message.success('매핑 삭제 완료');
      fetchMappings();
    } catch { message.error('삭제 실패'); }
  };

  const matchColor: Record<string, string> = { matched: 'green', unmatched: 'red', partial: 'orange' };

  const adColumns = [
    { title: '플랫폼', dataIndex: 'platform_id', render: (v: number) => platforms.find(p => p.id === v)?.name ?? v },
    { title: '캠페인', dataIndex: 'campaign_name' },
    { title: '광고유형', dataIndex: 'ad_type', render: (v: string | null) => v ?? '-' },
    { title: '지출', dataIndex: 'spend', render: (v: number) => `₩${Number(v).toLocaleString()}` },
    { title: '노출', dataIndex: 'impressions', render: (v: number) => v.toLocaleString() },
    { title: '클릭', dataIndex: 'clicks', render: (v: number) => v.toLocaleString() },
    { title: '전환', dataIndex: 'direct_conversions', render: (v: number | null) => v?.toLocaleString() ?? '-' },
    { title: '날짜', dataIndex: 'ad_date' },
    { title: '매칭', dataIndex: 'match_status', render: (v: string) => <Tag color={matchColor[v] ?? 'default'}>{v}</Tag> },
  ];

  const mapColumns = [
    { title: '플랫폼', dataIndex: 'platform_id', render: (v: number) => platforms.find(p => p.id === v)?.name ?? v },
    { title: '캠페인명', dataIndex: 'campaign_name' },
    { title: '상품', dataIndex: 'product_id', render: (v: number) => products.find(p => p.id === v)?.name ?? v },
    { title: '배분방식', dataIndex: 'allocation_method' },
    { title: '', key: 'action', render: (_: unknown, r: AdCampaignMapping) => (
      <Popconfirm title="삭제하시겠습니까?" onConfirm={() => handleDeleteMapping(r.id)}>
        <Button type="link" danger icon={<DeleteOutlined />} />
      </Popconfirm>
    )},
  ];

  return (
    <>
      {/* 광고 데이터 */}
      <Title level={4} style={{ marginBottom: 16 }}>광고 데이터</Title>
      <Space style={{ marginBottom: 16 }} wrap>
        <Select allowClear placeholder="플랫폼" style={{ width: 160 }}
          options={platforms.map(p => ({ value: p.id, label: p.name }))}
          onChange={v => setPlatformFilter(v)} />
        <RangePicker onChange={(_, ds) => ds[0] ? setDateRange([ds[0], ds[1]]) : setDateRange(null)} />
      </Space>
      <Table dataSource={ads} columns={adColumns} rowKey="id" loading={adsLoading} style={{ marginBottom: 32 }} />

      {/* 캠페인-상품 매핑 */}
      <Space style={{ justifyContent: 'space-between', width: '100%', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>캠페인-상품 매핑</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setMapModalOpen(true)}>매핑 추가</Button>
      </Space>
      <Table dataSource={mappings} columns={mapColumns} rowKey="id" loading={mapLoading} />

      <Modal title="캠페인-상품 매핑 추가" open={mapModalOpen}
        onCancel={() => setMapModalOpen(false)} onOk={() => mapForm.submit()} okText="추가">
        <Form form={mapForm} layout="vertical" onFinish={handleCreateMapping}>
          <Form.Item name="platform_id" label="플랫폼" rules={[{ required: true }]}>
            <Select options={platforms.map(p => ({ value: p.id, label: p.name }))} />
          </Form.Item>
          <Form.Item name="campaign_name" label="캠페인명" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="product_id" label="상품" rules={[{ required: true }]}>
            <Select showSearch optionFilterProp="label"
              options={products.map(p => ({ value: p.id, label: p.name }))} />
          </Form.Item>
          <Form.Item name="allocation_method" label="배분방식" rules={[{ required: true }]}>
            <Select options={[
              { value: 'equal', label: '균등 배분' },
              { value: 'revenue_ratio', label: '매출 비율' },
              { value: 'manual', label: '수동 지정' },
            ]} />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}
