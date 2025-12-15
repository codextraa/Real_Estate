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
  const initialState = {
    errors: {},
    success: "",
    formUserData: userData,
  };

  const [state, formActions, isPending] = useActionState(
    updateProfileAction,
    initialState,
  );

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [displaySuccess, setDisplaySuccess] = useState("");
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  const toggleShowPassword = () => {
    setShowPassword(!showPassword);
  };

  const toggleShowConfirmPassword = () => {
    setShowConfirmPassword(!showConfirmPassword);
  };

  const name =
    userRole === "Agent"
      ? state.formUserData.user.first_name +
        " " +
        state.formUserData.user.last_name
      : null;

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

  const initialFormData = getInitialFormData(state.formUserData, userRole);
  const [formData, setFormData] = useState(initialFormData);
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [bioContent, setBioContent] = useState(state.formUserData.bio || "");
  const [previewUrl, setPreviewUrl] = useState(state.formUserData.image_url);
  const textAreaRef = useRef(null);
  const fileInputRef = useRef(null);

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
    const fieldsChanged = Object.keys(currentData).some((key) => {
      return currentData[key] !== initialData[key];
    });

    const passwordFieldsChanged =
      currentPassword.length > 0 || currentConfirmPassword.length > 0;

    if (userRole === "Agent") {
      const bioChanged = currentBio !== initialBio;
      const imageChanged = currentImage !== initialImage;

      return (
        fieldsChanged || passwordFieldsChanged || bioChanged || imageChanged
      );
    }

    return fieldsChanged || passwordFieldsChanged;
  };

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

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setPreviewUrl(URL.createObjectURL(file));
    }
  };

  const handleIconClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const autoResize = (element) => {
    if (element) {
      element.style.height = "auto";
      element.style.height = element.scrollHeight + "px";
    }
  };

  useEffect(() => {
    if (state.success) {
      setDisplaySuccess(state.success);
      const timer = setTimeout(() => {
        setDisplaySuccess("");
        state.success = "";
      }, 2000);

      const newInitialFormData = getInitialFormData(
        state.formUserData,
        userRole,
      );
      setFormData(newInitialFormData);
      setBioContent(state.formUserData.bio || "");
      setPassword("");
      setConfirmPassword("");
      setPreviewUrl(state.formUserData.image_url);

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }

      return () => clearTimeout(timer);
    }
  }, [state.success]);

  useEffect(() => {
    const initial = getInitialFormData(userData, userRole);
    const initialBio = userData.bio || "";
    const initialImage = userData.image_url;

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
                  onChange={handleFileChange}
                  name="profile_image"
                  accept="image/*"
                  className={styles.fileInput}
                  disabled={isPending}
                />
              </div>
              {Object.keys(state.errors).length > 0 &&
                state.errors.image_url && (
                  <span className={styles.errorText}>
                    {state.errors.image_url}
                  </span>
                )}
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
                      disabled={isPending}
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
