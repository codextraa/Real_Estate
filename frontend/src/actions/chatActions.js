"use server";

import {
  getAIChatSession,
  deleteAIChatSession,
  postAIMessage,
  getAIMessage,
} from "@/libs/api";

export const getAIChatSessionAction = async (reportId) => {
  try {
    const response = await getAIChatSession(reportId);

    if (response.error) {
      return { error: response.error };
    }

    return response;
  } catch (error) {
    console.error(error);
    return { error: error.message || "An unexpected error occurred" };
  }
};

export const deleteAIChatSessionAction = async (sessionId) => {
  try {
    const response = await deleteAIChatSession(sessionId);

    if (response.error) {
      return { error: response.error };
    }

    return response;
  } catch (error) {
    console.error(error);
    return { error: error.message || "An unexpected error occurred" };
  }
};

export const postAIMessageAction = async (sessionId, prevState, formData) => {
  const content = formData.get("content");

  if (!content) {
    return { error: "Content is required" };
  }

  try {
    const response = await postAIMessage({
      session: sessionId,
      content: content,
    });

    if (response.error) {
      return { error: response.error };
    }

    return response;
  } catch (error) {
    console.error(error);
    return { error: error.message || "An unexpected error occurred" };
  }
};

export const getAIMessageAction = async (messageId) => {
  try {
    const response = await getAIMessage(messageId);
    return response;
  } catch (error) {
    console.error(error);
    return { error: error.message || "An unexpected error occurred" };
  }
};
