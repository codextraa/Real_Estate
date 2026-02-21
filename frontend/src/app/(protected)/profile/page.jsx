import { getUser, getAgent } from "@/libs/api";
import { getUserIdAction, getUserRoleAction } from "@/actions/authActions";
import { redirect } from "next/navigation";

export default async function ProfileRedirectPage() {
  const userId = await getUserIdAction();
  const userRole = await getUserRoleAction();

  let response;
  if (userRole === "Agent") {
    response = await getAgent(userId);
  } else {
    response = await getUser(userId);
  }

  if (response.error) {
    console.error(response.error);
    throw new Error(response.error);
  }

  const userSlug = userRole === "Agent" ? response.user.slug : response.slug;
  const userDataId = userRole === "Agent" ? response.user.id : response.id;

  if (!userSlug || !userDataId) {
    throw new Error("User slug not found");
  }

  // redirect(`/profile/${userSlug}?id=${userDataId}&role=${userRole}`);
  redirect(`/profile/${userSlug}`);
}
