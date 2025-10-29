import { notFound } from "next/navigation";
import { getUser, getAgent } from "@/libs/api";
import Image from "next/image";
import { getUserIdAction, getUserRoleAction } from "@/actions/authActions";
import ProfileWrapper from "@/components/wrappers/ProfileWrapper";

export default async function ProfilePage() {
  const user_id = await getUserIdAction();
  const user_role = await getUserRoleAction();
  const imgUrl = "/real-estate/real-estate.jpg";

  let response;
  if (user_role === "Agent") {
    response = await getAgent(user_id);
  } else {
    response = await getUser(user_id);
  }

  if (response.error) {
    return notFound();
  }

  return (
    <>
      <Image src={imgUrl} alt="background" fill priority />
      <ProfileWrapper userData={response} />
    </>
  );
}
