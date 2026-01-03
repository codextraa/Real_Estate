import { notFound } from "next/navigation";
import { getUser, getAgent } from "@/libs/api";
import Image from "next/image";
import { getUserIdAction, getUserRoleAction } from "@/actions/authActions";
import ProfileCard from "@/components/cards/ProfileCard";
import styles from "@/styles/ProfilePage.module.css";

export default async function ProfilePage({ params, searchParams }) {
  const urlParams = await params;
  const urlSearchParams = await searchParams;
  const slug = urlParams.slug;
  let userId = urlSearchParams.user_id;
  let userRole = urlSearchParams.user_role;
  const imgUrl = "/real-estate/real-estate.jpg";

  if (!userId && !userRole) {
    userId = await getUserIdAction();
    userRole = await getUserRoleAction();
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
          <ProfileCard
            userData={response}
            userId={userId}
            userRole={userRole}
          />
        </div>
      </div>
    </>
  );
}
