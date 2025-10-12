import { notFound } from "next/navigation";
import { getUser, getAgent } from "@/libs/api";
import ProfileCard from "@/components/cards/ProfileCard";

export default async function ProfilePage({ searchParams }) {
  const { id, role } = await searchParams;

  let response;
  if (role === "Agent") {
    response = await getAgent(id);
  } else {
    response = await getUser(id);
  }

  if (response.error) {
    return notFound();
  }

  return <ProfileCard userData={response} />;
}
