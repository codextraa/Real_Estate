"use server";
import { createReport, deleteReport, getReport } from "@/libs/api";

export const createReportAction = async (data) => {
  try {
    const response = await createReport({ data });

    if (response.error) {
      return { error: response.error };
    }

    return { success: response.success, data: response.data };
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

    return { data: response.data };
  } catch (error) {
    console.error(error);
    return { error: error.message || "An unexpected error occurred" };
  }
};
