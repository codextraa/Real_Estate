import Image from "next/image";
import { notFound } from "next/navigation";
import { getUser, getAgent } from "@/libs/api";
import { updateUserAction } from "@/actions/userActions";
import { getUserIdAction, getUserRoleAction } from "@/actions/authActions";
import ProfileForm from "@/components/forms/ProfileForm";
import styles from "@/styles/ProfilePage.module.css";
import { redirect } from "next/navigation";

export default async function EditPage({ params }) {
  const urlParams = await params;
  const slug = urlParams.slug;
  const userId = await getUserIdAction();
  const userRole = await getUserRoleAction();
  const imgUrl = "/real-estate/real-estate.jpg";

  if (!userId || !userRole) {
    redirect("/");
  }

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

  const containerClassStyle = `${styles.profileCardContainer} ${
    userRole === "Agent" ? styles.profileCardContainerAgent : ""
  }`;

  return (
    <>
      <div className={styles.profileImageWrapper}>
        <Image
          className={styles.profilePageBackgroundImage}
          src={imgUrl}
          alt="background"
          fill
          priority
        />
      </div>
      <div className={styles.profilePageWrapper}>
        <div className={containerClassStyle}>
          <ProfileForm
            userData={response}
            userRole={userRole}
            updateProfileAction={updateProfileAction}
          />
        </div>
      </div>
    </>
  );
}
