import { useEffect, useState } from 'react';
import {
  Tabs, Table, Button, Modal, Form, Input, InputNumber, Select, DatePicker,
  message, Space, Typography,
} from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import api from '../api/client';
import type { CostCategory, Product, Platform } from '../types';

const { Title } = Typography;

interface VariableCost {
  id: number;
  product_id: number;
  cost_category_id: number;
  amount: number;
  per_unit: boolean;
}

interface Campaign {
  id: number;
  name: string;
  platform_id: number | null;
  allocation_method: string;
  start_date: string | null;
  end_date: string | null;
}

interface MarketingCost {
  id: number;
  campaign_id: number | null;
  cost_category_id: number;
  product_id: number | null;
  amount: number;
  cost_date: string;
}

/* ── 비용 카테고리 ───────────────────────────────── */
function CostCategoriesTab() {
  const [data, setData] = useState<CostCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [form] = Form.useForm();

  const fetch = async () => {
    setLoading(true);
    try { setData((await api.get('/costs/categories')).data); } finally { setLoading(false); }
  };
  useEffect(() => { fetch(); }, []);

  const handleCreate = async (values: { name: string; type: string }) => {
    try {
      await api.post('/costs/categories', values);
      message.success('카테고리 추가 완료');
      setModalOpen(false);
      form.resetFields();
      fetch();
    } catch { message.error('추가 실패'); }
  };

  return (
    <>
      <Space style={{ justifyContent: 'space-between', width: '100%', marginBottom: 16 }}>
        <span />
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>카테고리 추가</Button>
      </Space>
      <Table dataSource={data} rowKey="id" loading={loading} columns={[
        { title: '이름', dataIndex: 'name' },
        { title: '유형', dataIndex: 'type' },
      ]} />
      <Modal title="비용 카테고리 추가" open={modalOpen} onCancel={() => setModalOpen(false)} onOk={() => form.submit()} okText="추가">
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="name" label="이름" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="type" label="유형" rules={[{ required: true }]}>
            <Select options={[
              { value: 'fixed', label: '고정비' },
              { value: 'variable', label: '변동비' },
              { value: 'marketing', label: '마케팅' },
            ]} />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}

/* ── 변동비 ──────────────────────────────────────── */
function VariableCostsTab() {
  const [data, setData] = useState<VariableCost[]>([]);
  const [categories, setCategories] = useState<CostCategory[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [form] = Form.useForm();

  const fetch = async () => {
    setLoading(true);
    try { setData((await api.get('/costs/variable')).data); } finally { setLoading(false); }
  };
  useEffect(() => {
    fetch();
    api.get('/costs/categories').then(r => setCategories(r.data));
    api.get('/products').then(r => setProducts(r.data));
  }, []);

  const handleCreate = async (values: { product_id: number; cost_category_id: number; amount: number; per_unit: boolean }) => {
    try {
      await api.post('/costs/variable', { ...values, amount: String(values.amount) });
      message.success('변동비 추가 완료');
      setModalOpen(false);
      form.resetFields();
      fetch();
    } catch { message.error('추가 실패'); }
  };

  return (
    <>
      <Space style={{ justifyContent: 'space-between', width: '100%', marginBottom: 16 }}>
        <span />
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>변동비 추가</Button>
      </Space>
      <Table dataSource={data} rowKey="id" loading={loading} columns={[
        { title: '상품', dataIndex: 'product_id', render: (v: number) => products.find(p => p.id === v)?.name ?? v },
        { title: '카테고리', dataIndex: 'cost_category_id', render: (v: number) => categories.find(c => c.id === v)?.name ?? v },
        { title: '금액', dataIndex: 'amount', render: (v: number) => `₩${Number(v).toLocaleString()}` },
        { title: '단위당', dataIndex: 'per_unit', render: (v: boolean) => v ? '예' : '아니오' },
      ]} />
      <Modal title="변동비 추가" open={modalOpen} onCancel={() => setModalOpen(false)} onOk={() => form.submit()} okText="추가">
        <Form form={form} layout="vertical" onFinish={handleCreate} initialValues={{ per_unit: true }}>
          <Form.Item name="product_id" label="상품" rules={[{ required: true }]}>
            <Select showSearch optionFilterProp="label"
              options={products.map(p => ({ value: p.id, label: p.name }))} />
          </Form.Item>
          <Form.Item name="cost_category_id" label="비용 카테고리" rules={[{ required: true }]}>
            <Select options={categories.map(c => ({ value: c.id, label: c.name }))} />
          </Form.Item>
          <Form.Item name="amount" label="금액" rules={[{ required: true }]}><InputNumber style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="per_unit" label="단위당 여부" rules={[{ required: true }]}>
            <Select options={[{ value: true, label: '예' }, { value: false, label: '아니오' }]} />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}

/* ── 캠페인 ──────────────────────────────────────── */
function CampaignsTab() {
  const [data, setData] = useState<Campaign[]>([]);
  const [platforms, setPlatforms] = useState<Platform[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [form] = Form.useForm();

  const fetch = async () => {
    setLoading(true);
    try { setData((await api.get('/costs/campaigns')).data); } finally { setLoading(false); }
  };
  useEffect(() => {
    fetch();
    api.get('/platforms').then(r => setPlatforms(r.data));
  }, []);

  const handleCreate = async (values: { name: string; platform_id?: number; allocation_method: string; dates?: [any, any] }) => {
    try {
      await api.post('/costs/campaigns', {
        name: values.name,
        platform_id: values.platform_id ?? null,
        allocation_method: values.allocation_method,
        start_date: values.dates?.[0]?.format('YYYY-MM-DD') ?? null,
        end_date: values.dates?.[1]?.format('YYYY-MM-DD') ?? null,
      });
      message.success('캠페인 추가 완료');
      setModalOpen(false);
      form.resetFields();
      fetch();
    } catch { message.error('추가 실패'); }
  };

  return (
    <>
      <Space style={{ justifyContent: 'space-between', width: '100%', marginBottom: 16 }}>
        <span />
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>캠페인 추가</Button>
      </Space>
      <Table dataSource={data} rowKey="id" loading={loading} columns={[
        { title: '캠페인명', dataIndex: 'name' },
        { title: '플랫폼', dataIndex: 'platform_id', render: (v: number | null) => platforms.find(p => p.id === v)?.name ?? '-' },
        { title: '배분방식', dataIndex: 'allocation_method' },
        { title: '시작일', dataIndex: 'start_date', render: (v: string | null) => v ?? '-' },
        { title: '종료일', dataIndex: 'end_date', render: (v: string | null) => v ?? '-' },
      ]} />
      <Modal title="캠페인 추가" open={modalOpen} onCancel={() => setModalOpen(false)} onOk={() => form.submit()} okText="추가">
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="name" label="캠페인명" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="platform_id" label="플랫폼">
            <Select allowClear options={platforms.map(p => ({ value: p.id, label: p.name }))} />
          </Form.Item>
          <Form.Item name="allocation_method" label="배분방식" rules={[{ required: true }]}>
            <Select options={[
              { value: 'equal', label: '균등 배분' },
              { value: 'revenue_ratio', label: '매출 비율' },
              { value: 'manual', label: '수동 지정' },
            ]} />
          </Form.Item>
          <Form.Item name="dates" label="기간">
            <DatePicker.RangePicker style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}

/* ── 마케팅비 ────────────────────────────────────── */
function MarketingCostsTab() {
  const [data, setData] = useState<MarketingCost[]>([]);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [categories, setCategories] = useState<CostCategory[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [form] = Form.useForm();

  const fetch = async () => {
    setLoading(true);
    try { setData((await api.get('/costs/marketing')).data); } finally { setLoading(false); }
  };
  useEffect(() => {
    fetch();
    api.get('/costs/campaigns').then(r => setCampaigns(r.data));
    api.get('/costs/categories').then(r => setCategories(r.data));
    api.get('/products').then(r => setProducts(r.data));
  }, []);

  const handleCreate = async (values: { campaign_id?: number; cost_category_id: number; product_id?: number; amount: number; cost_date: any }) => {
    try {
      await api.post('/costs/marketing', {
        campaign_id: values.campaign_id ?? null,
        cost_category_id: values.cost_category_id,
        product_id: values.product_id ?? null,
        amount: String(values.amount),
        cost_date: values.cost_date.format('YYYY-MM-DD'),
      });
      message.success('마케팅비 추가 완료');
      setModalOpen(false);
      form.resetFields();
      fetch();
    } catch { message.error('추가 실패'); }
  };

  return (
    <>
      <Space style={{ justifyContent: 'space-between', width: '100%', marginBottom: 16 }}>
        <span />
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>마케팅비 추가</Button>
      </Space>
      <Table dataSource={data} rowKey="id" loading={loading} columns={[
        { title: '캠페인', dataIndex: 'campaign_id', render: (v: number | null) => campaigns.find(c => c.id === v)?.name ?? '-' },
        { title: '카테고리', dataIndex: 'cost_category_id', render: (v: number) => categories.find(c => c.id === v)?.name ?? v },
        { title: '상품', dataIndex: 'product_id', render: (v: number | null) => products.find(p => p.id === v)?.name ?? '-' },
        { title: '금액', dataIndex: 'amount', render: (v: number) => `₩${Number(v).toLocaleString()}` },
        { title: '날짜', dataIndex: 'cost_date' },
      ]} />
      <Modal title="마케팅비 추가" open={modalOpen} onCancel={() => setModalOpen(false)} onOk={() => form.submit()} okText="추가">
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="campaign_id" label="캠페인">
            <Select allowClear options={campaigns.map(c => ({ value: c.id, label: c.name }))} />
          </Form.Item>
          <Form.Item name="cost_category_id" label="비용 카테고리" rules={[{ required: true }]}>
            <Select options={categories.map(c => ({ value: c.id, label: c.name }))} />
          </Form.Item>
          <Form.Item name="product_id" label="상품">
            <Select allowClear showSearch optionFilterProp="label"
              options={products.map(p => ({ value: p.id, label: p.name }))} />
          </Form.Item>
          <Form.Item name="amount" label="금액" rules={[{ required: true }]}><InputNumber style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="cost_date" label="날짜" rules={[{ required: true }]}><DatePicker style={{ width: '100%' }} /></Form.Item>
        </Form>
      </Modal>
    </>
  );
}

/* ── 메인 페이지 ─────────────────────────────────── */
export default function CostsPage() {
  return (
    <>
      <Title level={4} style={{ marginBottom: 16 }}>비용 관리</Title>
      <Tabs items={[
        { key: 'categories', label: '비용 카테고리', children: <CostCategoriesTab /> },
        { key: 'variable', label: '변동비', children: <VariableCostsTab /> },
        { key: 'campaigns', label: '캠페인', children: <CampaignsTab /> },
        { key: 'marketing', label: '마케팅비', children: <MarketingCostsTab /> },
      ]} />
    </>
  );
}
