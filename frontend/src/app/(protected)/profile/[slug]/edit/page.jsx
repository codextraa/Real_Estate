import Image from "next/image";
import { notFound } from "next/navigation";
import { getUser, getAgent } from "@/libs/api";
import { updateUserAction } from "@/actions/userActions";
import { getUserIdAction, getUserRoleAction } from "@/actions/authActions";
import ProfileForm from "@/components/forms/ProfileForm";
import styles from "@/styles/ProfilePage.module.css";

export default async function EditPage({ params }) {
  const urlParams = await params;
  const slug = urlParams.slug;
  const userId = await getUserIdAction();
  const userRole = await getUserRoleAction();
  const imgUrl = "/real-estate/real-estate.jpg";

  let response;
  let response_slug;
  if (userRole === "Agent") {
    response = await getAgent(userId);
    response_slug = response.user.slug;
  } else {
    response = await getUser(userId);
    response_slug = response.slug;
  }

  if (response.error || slug !== response_slug) {
    return notFound();
  }

  const updateProfileAction =
    userRole === "Agent"
      ? updateUserAction.bind(null, response.user.id, userRole)
      : updateUserAction.bind(null, response.id, userRole);

  return (
    <div className={styles.profilePageBackground}>
      <Image src={imgUrl} alt="background" fill priority />
      <div className={styles.profileCardContainer}>
        <ProfileForm
          userData={response}
          userRole={userRole}
          updateProfileAction={updateProfileAction}
        />
      </div>
    </div>
  );
}
