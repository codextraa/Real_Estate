import Form from "next/form";
import { FormButton } from "@/components/buttons/Buttons";
import styles from "./ProfileForm.module.css";
import { updateUserAction } from "@/actions/userActions";
import { useActionState } from "react";

export default function ProfileForm({ userData }) {
  const initialState = {
    errors: {},
    success: "",
    formEmailAddress: "",
    formFirstName: "",
    formLastName: "",
    formUsername: "",
  };

  const [state, formActions, isPending] = useActionState(
    updateUserAction.bind(userData.id, null, userData),
    initialState,
  );

  // error handling baki

  return (
    <Form action={formActions} className={styles.Form}>
      <div className={styles.inputFormContainer}>
        <div className={styles.inputContainer}>
          <input
            type="email"
            id="email"
            name="email"
            placeholder="Email Address"
            disabled={isPending}
            defaultValue={state.formEmail}
            className={styles.input}
          />
        </div>
        <div className={styles.inputContainer}>
          <input
            type="text"
            id="first_name"
            name="first_name"
            placeholder="First Name"
            disabled={isPending}
            defaultValue={state.formFirstName}
            className={styles.input}
          />
        </div>
        <div className={styles.inputContainer}>
          <input
            type="text"
            id="last_name"
            name="last_name"
            placeholder="Last Name"
            disabled={isPending}
            defaultValue={state.formLastName}
            className={styles.input}
          />
        </div>
        <div className={styles.inputContainer}>
          <input
            type="text"
            id="username"
            name="username"
            placeholder="Username"
            disabled={isPending}
            defaultValue={state.formUsername}
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
