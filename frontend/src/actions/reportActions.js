"use server";
import { createReport, deleteReport, getReport } from "@/libs/api";

export const createReportAction = async (id) => {
  try {
    const response = await createReport({ property_id: id });

    if (response.error) {
      return { error: response.error };
    }

    return { success: response.success };
  } catch (error) {
    console.error(error);
    return { error: error.message || "An unexpected error occurred" };
  }
};

export const deleteReportAction = async (id) => {
  try {
    const response = await deleteReport(id);

    if (response.error) {
      return { error: response.error };
    }

    return { success: response.success };
  } catch (error) {
    console.error(error);
    return { error: error.message || "An unexpected error occurred" };
  }
};

export const getReportAction = async (id) => {
  try {
    const response = await getReport(id);

    if (response.error) {
      return { error: response.error };
    }

    return response;
  } catch (error) {
    console.error(error);
    return { error: error.message || "An unexpected error occurred" };
  }
};
