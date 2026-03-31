export interface User {
  id: number;
  username: string;
  role: string;
}

export interface Platform {
  id: number;
  name: string;
  type: string;
  fee_rate: number;
  vat_included: boolean;
  site_identifier: string | null;
  seller_id: string | null;
}

export interface Product {
  id: number;
  name: string;
  sku: string;
  base_cost: number;
  category: string;
}

export interface PlatformProduct {
  id: number;
  product_id: number;
  platform_id: number;
  platform_product_id: string;
  platform_product_name: string;
  selling_price: number | null;
  platform_fee_rate: number | null;
  sale_status: string | null;
  site: string | null;
  matched_by: string;
}

export interface UploadResponse {
  upload_id: number;
  record_count: number;
  matched_count: number;
  unmatched_count: number;
}

export interface UploadHistory {
  id: number;
  platform_id: number;
  data_type: string;
  file_name: string;
  record_count: number;
  matched_count: number;
  unmatched_count: number;
  period_start: string;
  period_end: string;
  uploaded_at: string;
}

export interface CostCategory {
  id: number;
  name: string;
  type: string;
}

export interface PlatformProfit {
  platform_name: string;
  platform_id: number;
  revenue: number;
  cost_of_goods: number;
  platform_fee: number;
  coupon_cost: number;
  refund_shipping_cost: number;
  ad_cost: number;
  marketing_cost: number;
  variable_cost: number;
  net_profit: number;
  profit_rate: number;
}

export interface ProfitByProduct {
  product_id: number;
  product_name: string;
  sku: string;
  platforms: PlatformProfit[];
  total_revenue: number;
  total_net_profit: number;
  total_profit_rate: number;
}

export interface ChangeEvent {
  id: number;
  event_type_id: number;
  product_id: number | null;
  platform_id: number | null;
  description: string;
  change_details: Record<string, unknown>;
  event_date: string;
  created_at: string;
}

export interface EventType {
  id: number;
  name: string;
  is_default: boolean;
}

export interface AdData {
  id: number;
  platform_id: number;
  campaign_name: string;
  ad_type: string | null;
  spend: number;
  impressions: number;
  clicks: number;
  direct_conversions: number | null;
  ad_date: string;
  match_status: string;
}

export interface AdCampaignMapping {
  id: number;
  platform_id: number;
  campaign_name: string;
  product_id: number;
  allocation_method: string;
}
