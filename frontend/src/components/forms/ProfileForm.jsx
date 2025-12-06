"use client";

import Form from "next/form";
import Link from "next/link";
import Image from "next/image";
import { useEffect, useRef } from "react";
import { FormButton } from "@/components/buttons/Buttons";
import { EyeButton } from "@/components/buttons/Buttons";
import { useActionState, useState } from "react";
import { GlobalButton, DeleteButton } from "@/components/buttons/Buttons";
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

  const [bioContent, setBioContent] = useState(state.formUserData.bio || "");
  const [previewUrl, setPreviewUrl] = useState(state.formUserData.image_url);

  const fileInputRef = useRef(null);
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setPreviewUrl(URL.createObjectURL(file)); // Create preview URL
    }
  };

  const handleIconClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click(); // Programmatically click the hidden file input
    }
  };

  useEffect(() => {
    if (state.success) {
      setDisplaySuccess(state.success);
      const timer = setTimeout(() => {
        setDisplaySuccess("");
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [state.success]);

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
      <div className={styles.profileDetailTitle}>Profile Information</div>
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
        <Form action={formActions} className={styles.Form}>
          <div className={styles.agentProfileContainer}>
            <div className={styles.inputImageContainer}>
              <div className={styles.ImageContainer}>
                <Image
                  className={styles.profileImage}
                  src={previewUrl}
                  alt="Profile Image"
                  width={203}
                  height={142}
                />
                <Image
                  className={styles.updateIcon} // cursor: pointer;
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
                  className={styles.fileInput} // display: none;
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
                    disabled={isPending}
                    value={bioContent}
                    onChange={(e) => setBioContent(e.target.value)}
                    maxLength={250}
                    className={styles.storedText}
                  />
                  <div className={styles.charCount}>
                    {bioContent.length} / 250
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
                      defaultValue={state.formUserData.user.first_name || ""}
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
                      defaultValue={state.formUserData.user.last_name || ""}
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
                      defaultValue={state.formUserData.user.username || ""}
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
                    defaultValue={state.formUserData.company_name || ""}
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
              <div className={styles.profileDetails}>
                <h1 className={styles.subTitle2}>Change Password</h1>
                <div className={styles.profileInfos}>
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
                  <Link href={`/profile/${state.formUserData.user.slug}`}>
                    <GlobalButton text="Cancel" />
                  </Link>
                </div>
                <div className={styles.formProfileButtons}>
                  <div className={styles.updateProfileButton}>
                    <FormButton
                      text="Update Profile"
                      pendingText="Updating..."
                      type="submit"
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
                defaultValue={state.formUserData.first_name || ""}
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
                defaultValue={state.formUserData.last_name || ""}
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
                defaultValue={state.formUserData.username || ""}
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
              <div className={styles.profileBoxLabel}>
                <label className={styles.profileLabel} htmlFor="password">
                  Password
                </label>
                <div className={styles.passwordInputContainer}>
                  <input
                    type={showPassword ? "text" : "password"}
                    id="password"
                    name="password"
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
                <Link href={`/profile/${state.formUserData.slug}`}>
                  <GlobalButton text="Cancel" />
                </Link>
              </div>
              <div className={styles.formProfileButtons}>
                <div className={styles.updateProfileButton}>
                  <FormButton
                    text="Update Profile"
                    pendingText="Updating..."
                    type="submit"
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
