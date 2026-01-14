/**
 * 案例相关类型定义
 */
import type { Dayjs } from 'dayjs';

export interface Case {
  case_id: number;
  title: string;
  description?: string;
  source_url: string;
  main_image?: string;
  images: string[];
  video_url?: string;
  brand_name?: string;
  brand_industry?: string;
  activity_type?: string;
  location?: string;
  tags: string[];
  score?: number;
  score_decimal?: string;
  favourite: number;
  publish_time?: string;
  author?: string;
  company_name?: string;
  company_logo?: string;
  agency_name?: string;
  created_at?: string;
  updated_at?: string;
}

export interface CaseSearchResult extends Case {
  similarity?: number;
  highlight?: {
    title?: string;
    description?: string;
  };
}

export interface SearchParams {
  query?: string;
  semantic_query?: string;
  search_type?: 'keyword' | 'semantic' | 'hybrid';
  brand_name?: string;
  brand_industry?: string;
  activity_type?: string;
  location?: string;
  tags?: string[];
  start_date?: string;
  end_date?: string;
  min_score?: number;
  sort_by?: 'relevance' | 'time' | 'score' | 'favourite';
  sort_order?: 'asc' | 'desc';
  page?: number;
  page_size?: number;
  min_similarity?: number;
}

export interface FacetItem {
  name: string;
  count: number;
}

export interface Facets {
  brands: FacetItem[];
  industries: FacetItem[];
  activity_types: FacetItem[];
  tags: FacetItem[];
  locations?: FacetItem[];
}

export interface SearchResponse {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  results: CaseSearchResult[];
  facets?: Facets;
}
