import { useEffect, useState } from 'react';
import { Table, Button, Modal, Form, Input, InputNumber, message, Space, Tag, Typography } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import api from '../api/client';
import type { Product, PlatformProduct } from '../types';

const { Title } = Typography;

export default function ProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [detailProduct, setDetailProduct] = useState<Product | null>(null);
  const [platformProducts, setPlatformProducts] = useState<PlatformProduct[]>([]);
  const [form] = Form.useForm();

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const resp = await api.get('/products');
      setProducts(resp.data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchProducts(); }, []);

  const handleCreate = async (values: { name: string; sku: string; base_cost: number; category: string }) => {
    try {
      await api.post('/products', { ...values, base_cost: String(values.base_cost) });
      message.success('상품 추가 완료');
      setModalOpen(false);
      form.resetFields();
      fetchProducts();
    } catch {
      message.error('상품 추가 실패');
    }
  };

  const showDetail = async (product: Product) => {
    setDetailProduct(product);
    const resp = await api.get(`/products/${product.id}/platform-products`);
    setPlatformProducts(resp.data);
  };

  const columns = [
    { title: '상품명', dataIndex: 'name', key: 'name' },
    { title: 'SKU', dataIndex: 'sku', key: 'sku' },
    { title: '원가', dataIndex: 'base_cost', key: 'base_cost', render: (v: number) => `₩${Number(v).toLocaleString()}` },
    { title: '카테고리', dataIndex: 'category', key: 'category' },
    { title: '', key: 'action', render: (_: unknown, record: Product) => (
      <Button type="link" onClick={() => showDetail(record)}>채널별 상품</Button>
    )},
  ];

  const ppColumns = [
    { title: '플랫폼', dataIndex: 'platform_id', key: 'platform_id' },
    { title: '마켓 상품번호', dataIndex: 'platform_product_id', key: 'platform_product_id' },
    { title: '마켓 상품명', dataIndex: 'platform_product_name', key: 'platform_product_name' },
    { title: '판매가', dataIndex: 'selling_price', key: 'selling_price',
      render: (v: number | null) => v ? `₩${Number(v).toLocaleString()}` : '-' },
    { title: '매칭', dataIndex: 'matched_by', key: 'matched_by',
      render: (v: string) => <Tag color={v === 'auto' ? 'green' : v === 'manual' ? 'blue' : 'red'}>{v}</Tag> },
  ];

  return (
    <>
      <Space style={{ justifyContent: 'space-between', width: '100%', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>상품 관리</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>상품 추가</Button>
      </Space>

      <Table dataSource={products} columns={columns} rowKey="id" loading={loading} />

      <Modal title="상품 추가" open={modalOpen} onCancel={() => setModalOpen(false)} onOk={() => form.submit()} okText="추가">
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="name" label="상품명" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="sku" label="SKU" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="base_cost" label="원가" rules={[{ required: true }]}><InputNumber style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="category" label="카테고리" rules={[{ required: true }]}><Input /></Form.Item>
        </Form>
      </Modal>

      <Modal title={`${detailProduct?.name} — 채널별 상품`} open={!!detailProduct}
        onCancel={() => setDetailProduct(null)} footer={null} width={800}>
        <Table dataSource={platformProducts} columns={ppColumns} rowKey="id" pagination={false} />
      </Modal>
    </>
  );
}
