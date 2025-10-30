// app/profile/[slug]/edit/page.jsx
import { notFound } from "next/navigation";
import { getUser, getAgent } from "@/libs/api";
import Image from "next/image";
import { getUserIdAction, getUserRoleAction } from "@/actions/authActions";
import ProfileForm from "@/components/forms/ProfileForm";  // Your form

export default async function EditPage({ params }) {
  const urlParams = await params;
  const slug = urlParams.slug;
  const user_id = await getUserIdAction();
  const user_role = await getUserRoleAction();
  const imgUrl = "/real-estate/real-estate.jpg";
  
  let response;
  if (user_role === "Agent") {
    response = await getAgent(user_id);
  } else {
    response = await getUser(user_id);
  }
  
  if (response.error || slug !== response.slug) {
    return notFound();
  }

  return (
    <>
      {/* <Image src={imgUrl} alt="background" fill priority /> */}
      <ProfileForm userData={response} userRole={user_role} />
    </>
  );
}