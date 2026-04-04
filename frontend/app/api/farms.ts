import axios from "axios";
import {
  Farm,
  WaterStressResponse,
  PaginatedSoilMoistureResponse,
  PaginatedWeatherResponse,
} from "../types/farm";

const API = axios.create({
  baseURL: "http://localhost:8000",
});

export const getFarms = (agronomist_id: number) =>
  API.get<Farm[]>(`/farms/`, { params: { agronomist_id } });

export const getFarm = (farmId: number) => API.get<Farm>(`/farms/${farmId}`);

export const getWaterStress = (farmId: number) =>
  API.get<WaterStressResponse>(`/farms/${farmId}/water-stress`);

export const getWeatherReadings = (farmId: number) =>
  API.get<PaginatedWeatherResponse>(`/farms/${farmId}/weather`);

export const getSoilMoistureReadings = (farmId: number) =>
  API.get<PaginatedSoilMoistureResponse>(`/farms/${farmId}/soil-moisture`);
