import { useEffect, useState } from 'react';
import { Upload, Button, Form, Select, DatePicker, Input, Card, Table, message, Typography, Alert } from 'antd';
import { UploadOutlined, InboxOutlined } from '@ant-design/icons';
import api from '../api/client';
import type { Platform, UploadHistory, UploadResponse } from '../types';

const { Title } = Typography;
const { Dragger } = Upload;
const { RangePicker } = DatePicker;

export default function UploadPage() {
  const [platforms, setPlatforms] = useState<Platform[]>([]);
  const [history, setHistory] = useState<UploadHistory[]>([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<UploadResponse | null>(null);
  const [form] = Form.useForm();

  useEffect(() => {
    api.get('/platforms').then(r => setPlatforms(r.data));
    api.get('/upload/history').then(r => setHistory(r.data));
  }, []);

  const handleUpload = async (values: { platform_id: number; data_type: string; period: [any, any]; password?: string; file: any }) => {
    setLoading(true);
    setResult(null);
    try {
      const formData = new FormData();
      formData.append('file', values.file.file);
      formData.append('platform_id', String(values.platform_id));
      formData.append('data_type', values.data_type);
      formData.append('period_start', values.period[0].format('YYYY-MM-DD'));
      formData.append('period_end', values.period[1].format('YYYY-MM-DD'));
      if (values.password) formData.append('password', values.password);

      const resp = await api.post('/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
      setResult(resp.data);
      message.success(`업로드 완료: ${resp.data.record_count}건 처리, ${resp.data.matched_count}건 매칭`);
      api.get('/upload/history').then(r => setHistory(r.data));
    } catch (e: any) {
      message.error(`업로드 실패: ${e.response?.data?.detail || '알 수 없는 오류'}`);
    } finally {
      setLoading(false);
    }
  };

  const dataTypeOptions = [
    { value: 'sales_summary', label: '판매 데이터 (기간 합산)' },
    { value: 'order', label: '주문 데이터 (개별)' },
    { value: 'ad', label: '광고 데이터' },
    { value: 'product_catalog', label: '상품 카탈로그' },
  ];

  const historyColumns = [
    { title: '파일명', dataIndex: 'file_name', key: 'file_name' },
    { title: '유형', dataIndex: 'data_type', key: 'data_type' },
    { title: '처리건수', dataIndex: 'record_count', key: 'record_count' },
    { title: '매칭', dataIndex: 'matched_count', key: 'matched_count' },
    { title: '미매칭', dataIndex: 'unmatched_count', key: 'unmatched_count' },
    { title: '기간', key: 'period', render: (_: unknown, r: UploadHistory) => `${r.period_start} ~ ${r.period_end}` },
    { title: '업로드일', dataIndex: 'uploaded_at', key: 'uploaded_at',
      render: (v: string) => new Date(v).toLocaleString('ko-KR') },
  ];

  return (
    <>
      <Title level={4}>데이터 업로드</Title>

      <Card style={{ marginBottom: 24 }}>
        <Form form={form} layout="vertical" onFinish={handleUpload}>
          <Form.Item name="platform_id" label="플랫폼" rules={[{ required: true }]}>
            <Select options={platforms.map(p => ({ value: p.id, label: p.name }))} placeholder="플랫폼 선택" />
          </Form.Item>
          <Form.Item name="data_type" label="데이터 유형" rules={[{ required: true }]}>
            <Select options={dataTypeOptions} placeholder="데이터 유형 선택" />
          </Form.Item>
          <Form.Item name="period" label="기간" rules={[{ required: true }]}>
            <RangePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="password" label="파일 비밀번호 (선택)">
            <Input.Password placeholder="비밀번호 보호 엑셀인 경우" />
          </Form.Item>
          <Form.Item name="file" label="파일" rules={[{ required: true }]} valuePropName="file"
            getValueFromEvent={(e) => e}>
            <Dragger beforeUpload={() => false} maxCount={1}>
              <p className="ant-upload-drag-icon"><InboxOutlined /></p>
              <p>클릭하거나 파일을 드래그하세요</p>
              <p className="ant-upload-hint">CSV, Excel 파일 지원</p>
            </Dragger>
          </Form.Item>
          <Button type="primary" htmlType="submit" loading={loading} icon={<UploadOutlined />}>업로드</Button>
        </Form>
      </Card>

      {result && (
        <Alert type={result.unmatched_count > 0 ? 'warning' : 'success'} showIcon
          message={`처리 완료: ${result.record_count}건 중 ${result.matched_count}건 매칭, ${result.unmatched_count}건 미매칭`}
          style={{ marginBottom: 24 }} />
      )}

      <Title level={5}>업로드 이력</Title>
      <Table dataSource={history} columns={historyColumns} rowKey="id" />
    </>
  );
}
