"use client";

import Form from "next/form";
import Link from "next/link";
import Image from "next/image";
import { useEffect, useRef, useActionState, useState } from "react";
import {
  FormButton,
  EyeButton,
  DeleteButton,
} from "@/components/buttons/Buttons";
import UpdateAlert from "@/components/alerts/UpdateAlert";
import DeleteModal from "@/components/modals/DeleteModal";
import styles from "./ProfileForm.module.css";

export default function ProfileForm({
  userData,
  userRole,
  updateProfileAction,
}) {
  // Initial state for useActionState, contains form data and error/success handling
  const initialState = {
    errors: {},
    success: "",
    formUserData: userData,
    initialUserData: userData,
  };

  const [state, formActions, isPending] = useActionState(
    updateProfileAction,
    initialState,
  );

  // Client-side state for UI/form management
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [displaySuccess, setDisplaySuccess] = useState("");
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  const name =
    userRole === "Agent"
      ? state.formUserData.user.first_name +
        " " +
        state.formUserData.user.last_name
      : null;

  // Helper function to extract relevant form fields based on user role
  const getInitialFormData = (data, role) => {
    if (role === "Agent") {
      return {
        first_name: data.user.first_name || "",
        last_name: data.user.last_name || "",
        username: data.user.username || "",
        bio: data.bio || "",
        company_name: data.company_name || "",
      };
    } else {
      return {
        first_name: data.first_name || "",
        last_name: data.last_name || "",
        username: data.username || "",
      };
    }
  };

  // Initialize client-side form states using the data from the useActionState's state
  const initialFormData = getInitialFormData(state.formUserData, userRole);
  const [formData, setFormData] = useState(initialFormData);
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [bioContent, setBioContent] = useState(state.formUserData.bio || "");
  // previewUrl holds the server image URL initially, or a client Blob URL after file selection
  const [previewUrl, setPreviewUrl] = useState(state.formUserData.image_url);
  const [localImageError, setLocalImageError] = useState("");
  const textAreaRef = useRef(null);
  const fileInputRef = useRef(null);

  /**
   * Checks if any client-side form state differs from the initial server data.
   */
  const checkForChanges = (
    currentData,
    initialData,
    currentBio,
    initialBio,
    currentImage,
    initialImage,
    currentPassword,
    currentConfirmPassword,
  ) => {
    // Check text/input fields
    const fieldsChanged = Object.keys(currentData).some((key) => {
      return currentData[key] !== initialData[key];
    });

    // Check password fields
    const passwordFieldsChanged =
      currentPassword.length > 0 || currentConfirmPassword.length > 0;

    if (userRole === "Agent") {
      // Check bio and image
      const bioChanged = currentBio !== initialBio;
      const imageChanged = currentImage !== initialImage;

      return (
        fieldsChanged || passwordFieldsChanged || bioChanged || imageChanged
      );
    }

    return fieldsChanged || passwordFieldsChanged;
  };

  // Input change handlers
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleBioChange = (e) => {
    setBioContent(e.target.value);
  };

  const handlePasswordChange = (e) => {
    setPassword(e.target.value);
  };

  const handleConfirmPasswordChange = (e) => {
    setConfirmPassword(e.target.value);
  };

  // Reset previewUrl back to server image and file input to empty
  const resetImageInput = () => {
    setPreviewUrl(state.formUserData.image_url);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  /**
   * Handles file selection and creates a temporary Blob URL for immediate preview.
   * This Blob URL is what triggers 'hasUnsavedChanges'.
   */
  const handleImageChange = (e) => {
    const file = e.target.files[0];

    if (!file) {
      return;
    }

    setLocalImageError("");
    const validTypes = ["image/jpeg", "image/png", "image/jpg"];
    const isInvalidType = !validTypes.includes(file.type);
    const isTooLarge = file.size > 2 * 1024 * 1024;

    if (isInvalidType || isTooLarge) {
      const msg = isInvalidType
        ? "Only JPG, JPEG and PNG images are allowed."
        : "Image size should not exceed 2MB.";

      setLocalImageError(msg);
      resetImageInput();
      return;
    }

    // Clean up the old memory-stored URL before creating a new one
    if (previewUrl.startsWith("blob:")) {
      URL.revokeObjectURL(previewUrl);
    }

    setPreviewUrl(URL.createObjectURL(file));
  };

  const handleIconClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  // Auto resize logic for textarea
  const autoResize = (element) => {
    if (element) {
      element.style.height = "auto";
      element.style.height = element.scrollHeight + "px";
    }
  };

  // Reset local image error in submission
  useEffect(() => {
    if (isPending) {
      setLocalImageError("");
    }
  }, [isPending]);

  // If the server returns an image error, reset the local preview and file input
  useEffect(() => {
    if (state.errors && state.errors.image_url) {
      resetImageInput();
    }
  }, [state.errors]);

  useEffect(() => {
    if (state.success) {
      setDisplaySuccess(state.success);
      const timer = setTimeout(() => {
        setDisplaySuccess("");
        state.success = "";
      }, 2000);

      // RESET ALL CLIENT-SIDE FORM STATES to match the new, successful data.
      const newInitialFormData = getInitialFormData(
        state.formUserData,
        userRole,
      );
      setFormData(newInitialFormData);
      setBioContent(state.formUserData.bio || "");
      setPassword("");
      setConfirmPassword("");
      setLocalImageError("");
      resetImageInput();

      return () => clearTimeout(timer);
    }
  }, [state.success]);

  useEffect(() => {
    // Get the original data from the props (which is re-fetched/re-rendered
    // from the server via revalidatePath after a successful submission)
    const initial = getInitialFormData(userData, userRole);
    const initialBio = userData.bio || "";
    const initialImage = state.formUserData.image_url;

    // Check for differences between current client state and initial server state
    const changes = checkForChanges(
      formData,
      initial,
      bioContent,
      initialBio,
      previewUrl,
      initialImage,
      password,
      confirmPassword,
    );

    setHasUnsavedChanges(changes);
  }, [
    formData,
    bioContent,
    previewUrl,
    password,
    confirmPassword,
    userData,
    userRole,
  ]);

  // Textarea resize logic
  useEffect(() => {
    autoResize(textAreaRef.current);
  }, [bioContent]);

  useEffect(() => {
    const handleResize = () => {
      autoResize(textAreaRef.current);
    };
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
    };
  }, []);

  // Toggle password visibility
  const toggleShowPassword = () => {
    setShowPassword(!showPassword);
  };

  const toggleShowConfirmPassword = () => {
    setShowConfirmPassword(!showConfirmPassword);
  };

  // Modal handler
  const openDeleteModal = () => {
    setIsDeleteModalOpen(true);
    document.body.style.overflow = "hidden";
  };

  const closeDeleteModal = () => {
    setIsDeleteModalOpen(false);
    document.body.style.overflow = "auto";
  };

  return (
    <div className={styles.profileInfoContainer}>
      <div className={styles.profileDetailTitle}>Edit Profile Information</div>
      <UpdateAlert hasUnsavedChanges={hasUnsavedChanges} />
      {isDeleteModalOpen && (
        <DeleteModal
          title="Are you sure you want to delete your account?"
          userData={userData}
          userRole={userRole}
          actionName="deleteUser"
          onCancel={closeDeleteModal}
        />
      )}
      {userRole === "Agent" ? (
        <Form action={formActions}>
          <div className={styles.agentProfileContainer}>
            <div className={styles.inputImageContainer}>
              <div className={styles.ImageContainer}>
                <Image
                  className={styles.profileImage}
                  src={previewUrl}
                  alt="Profile Image"
                  width={333}
                  height={250}
                />
                <Image
                  className={styles.updateIcon}
                  onClick={handleIconClick}
                  src="/assets/update-icon.svg"
                  alt="Update Icon"
                  width={38}
                  height={37}
                />
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleImageChange}
                  name="profile_image"
                  accept="image/*"
                  className={styles.fileInput}
                  disabled={isPending}
                />
                <input
                  type="hidden"
                  name="client_preview_url"
                  value={previewUrl}
                />
              </div>
              {localImageError ? (
                <span className={styles.errorText}>{localImageError}</span>
              ) : Object.keys(state.errors).length > 0 &&
                state.errors.image_url ? (
                <span className={styles.errorText}>
                  {state.errors.image_url}
                </span>
              ) : null}
            </div>
            <div className={styles.profileContainer}>
              <div className={styles.bioInfo}>
                <h1 className={styles.subTitle}>{name}</h1>
                <label className={styles.aboutMeLabel} htmlFor="bio">
                  About Me
                </label>
                <div className={styles.bioContainer}>
                  <textarea
                    id="bio"
                    name="bio"
                    ref={textAreaRef}
                    disabled={isPending}
                    value={bioContent}
                    onChange={handleBioChange}
                    maxLength={150}
                    className={styles.storedText}
                  />
                  <div className={styles.charCount}>
                    {bioContent.length} / 150
                  </div>
                </div>
                {Object.keys(state.errors).length > 0 && state.errors.bio && (
                  <span className={styles.errorText}>{state.errors.bio}</span>
                )}
              </div>
              <div className={styles.profileDetails}>
                <h1 className={styles.subTitle2}>Details</h1>
                <div className={styles.profileInfos}>
                  <div
                    className={`${styles.profileBoxLabel} ${styles.profileBoxLabelAgent}`}
                  >
                    <label className={styles.profileLabel} htmlFor="email">
                      Email Address
                    </label>
                    <input
                      type="email"
                      id="email"
                      disabled={true}
                      defaultValue={state.formUserData.user.email || ""}
                      className={styles.storedContent}
                    />
                    {Object.keys(state.errors).length > 0 &&
                      state.errors.email && (
                        <span className={styles.errorText}>
                          {state.errors.email}
                        </span>
                      )}
                  </div>
                  <div
                    className={`${styles.profileBoxLabel} ${styles.profileBoxLabelAgent}`}
                  >
                    <label className={styles.profileLabel} htmlFor="first_name">
                      First Name
                    </label>
                    <input
                      type="text"
                      id="first_name"
                      name="first_name"
                      disabled={isPending}
                      value={formData.first_name}
                      onChange={handleInputChange}
                      className={styles.storedContent}
                    />
                  </div>
                  <div
                    className={`${styles.profileBoxLabel} ${styles.profileBoxLabelAgent}`}
                  >
                    <label className={styles.profileLabel} htmlFor="last_name">
                      Last Name
                    </label>
                    <input
                      type="text"
                      id="last_name"
                      name="last_name"
                      disabled={isPending}
                      value={formData.last_name}
                      onChange={handleInputChange}
                      className={styles.storedContent}
                    />
                  </div>
                  <div
                    className={`${styles.profileBoxLabel} ${styles.profileBoxLabelAgent}`}
                  >
                    <label className={styles.profileLabel} htmlFor="username">
                      Username
                    </label>
                    <input
                      type="text"
                      id="username"
                      name="username"
                      disabled={isPending}
                      value={formData.username}
                      onChange={handleInputChange}
                      className={styles.storedContent}
                    />
                    {Object.keys(state.errors).length > 0 &&
                      state.errors.username && (
                        <span className={styles.errorText}>
                          {state.errors.username}
                        </span>
                      )}
                  </div>
                </div>
              </div>
              <div className={styles.profileDetails}>
                <h1 className={styles.subTitle2}>Company Information</h1>
                <div
                  className={`${styles.profileBoxLabel} ${styles.profileBoxLabelAgent}`}
                >
                  <label className={styles.profileLabel} htmlFor="company_name">
                    Company Name
                  </label>
                  <input
                    type="text"
                    id="company_name"
                    name="company_name"
                    disabled={isPending}
                    value={formData.company_name}
                    onChange={handleInputChange}
                    className={styles.storedContent}
                  />
                  {Object.keys(state.errors).length > 0 &&
                    state.errors.company_name && (
                      <span className={styles.errorText}>
                        {state.errors.company_name}
                      </span>
                    )}
                </div>
              </div>
              <div
                className={`${styles.passwordContainer} ${styles.passwordContainerAgent}`}
              >
                <h2
                  className={`${styles.changePasswordTitle} ${styles.changePasswordTitleAgent}`}
                >
                  Change Password
                </h2>
                <div
                  className={`${styles.wholePasswordContainer} ${styles.wholePasswordContainerAgent}`}
                >
                  <div
                    className={`${styles.profileBoxLabel} ${styles.profileBoxLabelAgent}`}
                  >
                    <label className={styles.profileLabel} htmlFor="password">
                      Password
                    </label>
                    <div className={styles.passwordInputContainer}>
                      <input
                        type={showPassword ? "text" : "password"}
                        id="password"
                        name="password"
                        value={password}
                        onChange={handlePasswordChange}
                        disabled={isPending}
                        className={styles.storedContent}
                      />
                      <EyeButton
                        action={toggleShowPassword}
                        showPassword={showPassword}
                        isPending={isPending}
                      />
                    </div>
                    {Object.keys(state.errors).length > 0 &&
                      state.errors.password && (
                        <span className={styles.errorText}>
                          {state.errors.password}
                        </span>
                      )}
                  </div>
                  <div
                    className={`${styles.profileBoxLabel} ${styles.profileBoxLabelAgent}`}
                  >
                    <label className={styles.profileLabel} htmlFor="c_password">
                      Confirm Password
                    </label>
                    <div className={styles.passwordInputContainer}>
                      <input
                        type={showConfirmPassword ? "text" : "password"}
                        id="c_password"
                        name="c_password"
                        value={confirmPassword}
                        onChange={handleConfirmPasswordChange}
                        disabled={isPending}
                        className={styles.storedContent}
                      />
                      <EyeButton
                        action={toggleShowConfirmPassword}
                        showPassword={showConfirmPassword}
                        isPending={isPending}
                      />
                    </div>
                    {Object.keys(state.errors).length > 0 &&
                      state.errors.c_password && (
                        <span className={styles.errorText}>
                          {state.errors.c_password}
                        </span>
                      )}
                  </div>
                </div>
              </div>
              {Object.keys(state.errors).length > 0 && state.errors.general && (
                <div
                  className={`${styles.errorContainer} ${styles.errorContainerAgent}`}
                >
                  {state.errors.general}
                </div>
              )}
              {displaySuccess && (
                <div
                  className={`${styles.successContainer} ${styles.successContainerAgent}`}
                >
                  {displaySuccess}
                </div>
              )}
              <div
                className={`${styles.buttonContainer} ${styles.buttonContainerAgent}`}
              >
                <div
                  className={`${styles.cancelProfileButton} ${styles.cancelProfileButtonAgent}`}
                >
                  <Link href={`/profile/${state.formUserData.user.slug}`}>
                    Cancel
                  </Link>
                </div>
                <div className={styles.formProfileButtons}>
                  <div
                    className={`${styles.updateProfileButton} ${styles.updateProfileButtonAgent}`}
                  >
                    <FormButton
                      text="Update Profile"
                      pendingText="Updating..."
                      type="submit"
                      className={`${styles.updateButton} ${styles.updateButtonAgent}`}
                    />
                  </div>
                  <div
                    className={`${styles.deleteProfileButton} ${styles.deleteProfileButtonAgent}`}
                  >
                    <DeleteButton
                      text="Delete Profile"
                      type="button"
                      onClick={openDeleteModal}
                      className={`${styles.deleteButton} ${styles.deleteButtonAgent}`}
                      disabled={isPending}
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </Form>
      ) : (
        <Form action={formActions}>
          <div className={`${styles.profileInfos} ${styles.profileInfosUser}`}>
            <div className={styles.profileBoxLabel}>
              <label className={styles.profileLabel} htmlFor="email">
                Email Address
              </label>
              <input
                type="email"
                id="email"
                disabled={isPending}
                defaultValue={state.formUserData.email || ""}
                className={styles.storedContent}
                readOnly
              />
            </div>
            <div className={styles.profileBoxLabel}>
              <label className={styles.profileLabel} htmlFor="first_name">
                First Name
              </label>
              <input
                type="text"
                id="first_name"
                name="first_name"
                disabled={isPending}
                value={formData.first_name}
                onChange={handleInputChange}
                className={styles.storedContent}
              />
              {Object.keys(state.errors).length > 0 &&
                state.errors.first_name && (
                  <span className={styles.errorText}>
                    {state.errors.first_name}
                  </span>
                )}
            </div>
            <div className={styles.profileBoxLabel}>
              <label className={styles.profileLabel} htmlFor="last_name">
                Last Name
              </label>
              <input
                type="text"
                id="last_name"
                name="last_name"
                disabled={isPending}
                value={formData.last_name}
                onChange={handleInputChange}
                className={styles.storedContent}
              />
              {Object.keys(state.errors).length > 0 &&
                state.errors.last_name && (
                  <span className={styles.errorText}>
                    {state.errors.last_name}
                  </span>
                )}
            </div>
            <div className={styles.profileBoxLabel}>
              <label className={styles.profileLabel} htmlFor="username">
                Username
              </label>
              <input
                type="text"
                id="username"
                name="username"
                disabled={isPending}
                value={formData.username}
                onChange={handleInputChange}
                className={styles.storedContent}
              />
              {Object.keys(state.errors).length > 0 &&
                state.errors.username && (
                  <span className={styles.errorText}>
                    {state.errors.username}
                  </span>
                )}
            </div>
            <div className={styles.passwordContainer}>
              <h2 className={styles.changePasswordTitle}>Change Password</h2>
              <div className={styles.wholePasswordContainer}>
                <div className={styles.profileBoxLabel}>
                  <label className={styles.profileLabel} htmlFor="password">
                    Password
                  </label>
                  <div className={styles.passwordInputContainer}>
                    <input
                      type={showPassword ? "text" : "password"}
                      id="password"
                      name="password"
                      value={password}
                      onChange={handlePasswordChange}
                      disabled={isPending}
                      className={styles.storedContent}
                    />
                    <EyeButton
                      action={toggleShowPassword}
                      showPassword={showPassword}
                      isPending={isPending}
                    />
                  </div>
                  {Object.keys(state.errors).length > 0 &&
                    state.errors.password && (
                      <span className={styles.errorText}>
                        {state.errors.password}
                      </span>
                    )}
                </div>
                <div className={styles.profileBoxLabel}>
                  <label className={styles.profileLabel} htmlFor="c_password">
                    Confirm Password
                  </label>
                  <div className={styles.passwordInputContainer}>
                    <input
                      type={showConfirmPassword ? "text" : "password"}
                      id="c_password"
                      name="c_password"
                      value={confirmPassword}
                      onChange={handleConfirmPasswordChange}
                      disabled={isPending}
                      className={styles.storedContent}
                    />
                    <EyeButton
                      action={toggleShowConfirmPassword}
                      showPassword={showConfirmPassword}
                      isPending={isPending}
                    />
                  </div>
                  {Object.keys(state.errors).length > 0 &&
                    state.errors.c_password && (
                      <span className={styles.errorText}>
                        {state.errors.c_password}
                      </span>
                    )}
                </div>
              </div>
            </div>
            {Object.keys(state.errors).length > 0 && state.errors.general && (
              <div className={styles.errorContainer}>
                {state.errors.general}
              </div>
            )}
            {displaySuccess && (
              <div className={styles.successContainer}>{displaySuccess}</div>
            )}
            <div className={styles.buttonContainer}>
              <div className={styles.cancelProfileButton}>
                <Link href={`/profile/${state.formUserData.slug}`}>Cancel</Link>
              </div>
              <div className={styles.formProfileButtons}>
                <div className={styles.updateProfileButton}>
                  <FormButton
                    text="Update Profile"
                    pendingText="Updating..."
                    type="submit"
                    className={styles.updateButton}
                  />
                </div>
                <div className={styles.deleteProfileButton}>
                  <DeleteButton
                    text="Delete Profile"
                    type="button"
                    onClick={openDeleteModal}
                    className={styles.deleteButton}
                    disabled={isPending}
                  />
                </div>
              </div>
            </div>
          </div>
        </Form>
      )}
    </div>
  );
}
