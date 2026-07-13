import axios from "axios";
import type { TripRequest, TripResponse } from "../types/trip";

const API_BASE_URL = "http://127.0.0.1:8000";

export async function planTrip(
  request: TripRequest
): Promise<TripResponse> {
  const response = await axios.post<TripResponse>(
    `${API_BASE_URL}/trip/`,
    request
  );

  return response.data;
}