import { notFound } from "next/navigation";
import { getUser, getAgent } from "@/libs/api";
import Image from "next/image";
import { getUserIdAction, getUserRoleAction } from "@/actions/authActions";
import ProfileCard from "@/components/cards/ProfileCard";

export default async function ProfilePage({ params }) {
  const urlParams = await params;
  const slug = urlParams.slug;
  const user_id = await getUserIdAction();
  const user_role = await getUserRoleAction();
  const imgUrl = "/real-estate/real-estate.jpg";

  let response;
  let response_slug;
  if (user_role === "Agent") {
    response = await getAgent(user_id);
    response_slug = response.user.slug;
  } else {
    response = await getUser(user_id);
    response_slug = response.slug;
  }

  if (response.error || slug !== response_slug) {
    return notFound();
  }

  return (
    <>
      <Image src={imgUrl} alt="background" fill priority />
      <ProfileCard userData={response} userRole={user_role} />
    </>
  );
}
