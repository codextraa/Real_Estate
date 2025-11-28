import { notFound } from "next/navigation";
import { getUser, getAgent } from "@/libs/api";
import Image from "next/image";
import { getUserIdAction, getUserRoleAction } from "@/actions/authActions";
import ProfileCard from "@/components/cards/ProfileCard";
import styles from "@/styles/ProfilePage.module.css";

export default async function ProfilePage({ params }) {
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
        <div className={styles.profileCardContainer}>
          <ProfileCard userData={response} userRole={userRole} />
        </div>
      </div>
    </>
  );
}
