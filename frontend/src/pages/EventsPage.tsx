import { useEffect, useState } from 'react';
import {
  Table, Button, Modal, Form, Input, Select, DatePicker, message, Space, Typography, Divider,
} from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import api from '../api/client';
import type { EventType, ChangeEvent, Product, Platform } from '../types';

const { Title } = Typography;
const { TextArea } = Input;
const { RangePicker } = DatePicker;

export default function EventsPage() {
  /* 이벤트 유형 */
  const [eventTypes, setEventTypes] = useState<EventType[]>([]);
  const [typeLoading, setTypeLoading] = useState(true);
  const [typeModalOpen, setTypeModalOpen] = useState(false);
  const [typeForm] = Form.useForm();

  /* 변경 이벤트 */
  const [events, setEvents] = useState<ChangeEvent[]>([]);
  const [evtLoading, setEvtLoading] = useState(true);
  const [evtModalOpen, setEvtModalOpen] = useState(false);
  const [evtForm] = Form.useForm();

  /* 필터 */
  const [filterProduct, setFilterProduct] = useState<number | undefined>();
  const [filterPlatform, setFilterPlatform] = useState<number | undefined>();
  const [filterDates, setFilterDates] = useState<[string, string] | null>(null);

  /* reference */
  const [products, setProducts] = useState<Product[]>([]);
  const [platforms, setPlatforms] = useState<Platform[]>([]);

  const fetchTypes = async () => {
    setTypeLoading(true);
    try { setEventTypes((await api.get('/events/types')).data); } finally { setTypeLoading(false); }
  };

  const fetchEvents = async () => {
    setEvtLoading(true);
    try {
      const params: Record<string, string> = {};
      if (filterProduct) params.product_id = String(filterProduct);
      if (filterPlatform) params.platform_id = String(filterPlatform);
      if (filterDates) { params.start_date = filterDates[0]; params.end_date = filterDates[1]; }
      setEvents((await api.get('/events', { params })).data);
    } finally { setEvtLoading(false); }
  };

  useEffect(() => {
    fetchTypes();
    fetchEvents();
    api.get('/products').then(r => setProducts(r.data));
    api.get('/platforms').then(r => setPlatforms(r.data));
  }, []);

  useEffect(() => { fetchEvents(); }, [filterProduct, filterPlatform, filterDates]);

  /* 이벤트 유형 생성 */
  const handleCreateType = async (values: { name: string }) => {
    try {
      await api.post('/events/types', values);
      message.success('이벤트 유형 추가 완료');
      setTypeModalOpen(false);
      typeForm.resetFields();
      fetchTypes();
    } catch { message.error('추가 실패'); }
  };

  /* 변경 이벤트 생성 */
  const handleCreateEvent = async (values: {
    event_type_id: number;
    product_id?: number;
    platform_id?: number;
    description: string;
    before_value?: string;
    after_value?: string;
    event_date: any;
  }) => {
    try {
      await api.post('/events', {
        event_type_id: values.event_type_id,
        product_id: values.product_id ?? null,
        platform_id: values.platform_id ?? null,
        description: values.description,
        change_details: { before: values.before_value ?? '', after: values.after_value ?? '' },
        event_date: values.event_date.format('YYYY-MM-DD'),
      });
      message.success('이벤트 추가 완료');
      setEvtModalOpen(false);
      evtForm.resetFields();
      fetchEvents();
    } catch { message.error('추가 실패'); }
  };

  return (
    <>
      {/* 이벤트 유형 관리 */}
      <Space style={{ justifyContent: 'space-between', width: '100%', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>이벤트 유형 관리</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setTypeModalOpen(true)}>유형 추가</Button>
      </Space>
      <Table dataSource={eventTypes} rowKey="id" loading={typeLoading} size="small" columns={[
        { title: '이름', dataIndex: 'name' },
        { title: '기본 유형', dataIndex: 'is_default', render: (v: boolean) => v ? '예' : '아니오' },
      ]} />

      <Divider />

      {/* 변경 이벤트 */}
      <Space style={{ justifyContent: 'space-between', width: '100%', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>변경 이벤트</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setEvtModalOpen(true)}>이벤트 추가</Button>
      </Space>
      <Space style={{ marginBottom: 16 }} wrap>
        <Select allowClear placeholder="상품" style={{ width: 180 }} showSearch optionFilterProp="label"
          options={products.map(p => ({ value: p.id, label: p.name }))}
          onChange={v => setFilterProduct(v)} />
        <Select allowClear placeholder="플랫폼" style={{ width: 160 }}
          options={platforms.map(p => ({ value: p.id, label: p.name }))}
          onChange={v => setFilterPlatform(v)} />
        <RangePicker onChange={(_, ds) => ds[0] ? setFilterDates([ds[0], ds[1]]) : setFilterDates(null)} />
      </Space>
      <Table dataSource={events} rowKey="id" loading={evtLoading} columns={[
        { title: '유형', dataIndex: 'event_type_id', render: (v: number) => eventTypes.find(t => t.id === v)?.name ?? v },
        { title: '상품', dataIndex: 'product_id', render: (v: number | null) => products.find(p => p.id === v)?.name ?? '-' },
        { title: '플랫폼', dataIndex: 'platform_id', render: (v: number | null) => platforms.find(p => p.id === v)?.name ?? '-' },
        { title: '설명', dataIndex: 'description', ellipsis: true },
        { title: '변경 내용', dataIndex: 'change_details', render: (v: Record<string, unknown>) => {
          const before = v?.before ?? '';
          const after = v?.after ?? '';
          return before || after ? `${before} → ${after}` : '-';
        }},
        { title: '이벤트 날짜', dataIndex: 'event_date' },
        { title: '생성일', dataIndex: 'created_at', render: (v: string) => v?.slice(0, 10) ?? '-' },
      ]} />

      {/* 유형 추가 모달 */}
      <Modal title="이벤트 유형 추가" open={typeModalOpen}
        onCancel={() => setTypeModalOpen(false)} onOk={() => typeForm.submit()} okText="추가">
        <Form form={typeForm} layout="vertical" onFinish={handleCreateType}>
          <Form.Item name="name" label="유형 이름" rules={[{ required: true }]}><Input /></Form.Item>
        </Form>
      </Modal>

      {/* 이벤트 추가 모달 */}
      <Modal title="변경 이벤트 추가" open={evtModalOpen}
        onCancel={() => setEvtModalOpen(false)} onOk={() => evtForm.submit()} okText="추가" width={600}>
        <Form form={evtForm} layout="vertical" onFinish={handleCreateEvent}>
          <Form.Item name="event_type_id" label="이벤트 유형" rules={[{ required: true }]}>
            <Select options={eventTypes.map(t => ({ value: t.id, label: t.name }))} />
          </Form.Item>
          <Form.Item name="product_id" label="상품">
            <Select allowClear showSearch optionFilterProp="label"
              options={products.map(p => ({ value: p.id, label: p.name }))} />
          </Form.Item>
          <Form.Item name="platform_id" label="플랫폼">
            <Select allowClear options={platforms.map(p => ({ value: p.id, label: p.name }))} />
          </Form.Item>
          <Form.Item name="description" label="설명" rules={[{ required: true }]}><TextArea rows={3} /></Form.Item>
          <Form.Item name="before_value" label="변경 전"><Input /></Form.Item>
          <Form.Item name="after_value" label="변경 후"><Input /></Form.Item>
          <Form.Item name="event_date" label="이벤트 날짜" rules={[{ required: true }]}><DatePicker style={{ width: '100%' }} /></Form.Item>
        </Form>
      </Modal>
    </>
  );
}
