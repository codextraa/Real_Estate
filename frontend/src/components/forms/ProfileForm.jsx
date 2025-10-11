import Form from "next/form";
import { FormButton } from "@/components/buttons/Buttons";
import styles from "./ProfileForm.module.css";

export default function ProfileForm() {
  const sabiq=11
  return (
  
    <Form action={sabiq} className={styles.Form}>
      <div className={styles.inputFormContainer}>
        <div className={styles.inputContainer}>
          <input
            type="email"
            id="email_address"
            name="email_address"
            placeholder="Email Address"
            className={styles.input}
          />
        </div>
        <div className={styles.inputContainer}>
          <input
            type="text"
            id="first_name"
            name="first_name"
            placeholder="First Name"
            className={styles.input}
          />
        </div>
        <div className={styles.inputContainer}>
          <input
            type="text"
            id="last_name"
            name="last_name"
            placeholder="Last Name"
            className={styles.input}
          />
        </div>
        <div className={styles.inputContainer}>
          <input
            type="text"
            id="username"
            name="username"
            placeholder="Username"
            className={styles.input}
          />
        </div>
        <div className={styles.buttonContainer}>
          <div className={styles.updateProfileButton}>
            <FormButton
              text="Update Profile"
              pendingText="Updating..."
              type="submit"
            />
          </div>
          <div className={styles.deleteProfileButton}>
            <FormButton
              text="Delete Profile"
              pendingText="Deleting..."
              type="submit"
            />
          </div>
        </div>
      </div>
    </Form>
  );
}
