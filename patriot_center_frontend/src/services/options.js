import { apiGet } from '../config/api';

export async function fetchOptions() {
  return apiGet('/meta/options');
}