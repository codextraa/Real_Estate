import { notFound } from "next/navigation";
import { getUser, getAgent } from "@/libs/api";
import Image from "next/image";
import { getUserIdAction, getUserRoleAction } from "@/actions/authActions";
import ProfileForm from "@/components/forms/ProfileForm";
import styles from "@/styles/ProfilePage.module.css";

export default async function EditPage({ params }) {
  const urlParams = await params;
  console.log("EditPage params:", urlParams);
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

  console.log("EditPage response:", response);
  console.log("slug:", slug);
  if (response.error || slug !== response_slug) {
    return notFound();
  }

  return (
    <div className={styles.profilePageBackground}>
      <Image src={imgUrl} alt="background" fill priority />
      <div className={styles.profileCardContainer}>
        <ProfileForm userData={response} userRole={user_role} />
      </div>
    </div>
  );
}
