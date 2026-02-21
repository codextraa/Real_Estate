"use client";

import { useState, useEffect, useActionState, useRef } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import Form from "next/form";
import { updatePropertyAction } from "@/actions/propertyActions";
import UpdateAlert from "@/components/alerts/UpdateAlert";
import { FormButton } from "@/components/buttons/Buttons";
import styles from "./CreateListingForm.module.css";

const uploadIcon = "/assets/upload-icon.svg";
const doneIcon = "/assets/done.svg";
const notDoneIcon = "/assets/not-done.svg";

export default function UpdateListingClient({ propertyId, initialData }) {
  const [formData, setFormData] = useState({
    title: initialData?.title || "",
    description: initialData?.description || "",
    country: initialData?.address?.country || "",
    state: initialData?.address?.state || "",
    city: initialData?.address?.city || "",
    area: initialData?.address?.area || "",
    street: initialData?.address?.street || "",
    house_no: initialData?.address?.house_no || "",
    flat_no: initialData?.address?.flat_no || "",
    beds: initialData?.beds || "",
    baths: initialData?.baths || "",
    area_sqft: initialData?.area_sqft || "",
    price: initialData?.price || "",
  });

  const [previewUrl, setPreviewUrl] = useState(initialData?.image_url || null);
  const [localImageError, setLocalImageError] = useState("");
  const fileInputRef = useRef(null);
  const textAreaRef = useRef(null);
  const router = useRouter();

  const [currentInitialData, setCurrentInitialData] = useState(initialData);
  const [displaySuccess, setDisplaySuccess] = useState("");

  const [state, formAction, isPending] = useActionState(
    (prevState, formData) =>
      updatePropertyAction(propertyId, prevState, formData),
    {
      errors: {},
      success: "",
      formPropertyData: initialData,
    },
  );

  const slugify = (text) => {
    return text
      .toString()
      .toLowerCase()
      .trim()
      .replace(/\s+/g, "-")
      .replace(/[^\w-]+/g, "")
      .replace(/--+/g, "-");
  };

  const isTitleChanged = formData.title !== currentInitialData?.title;
  const activeTitle = isTitleChanged
    ? formData.title
    : currentInitialData?.title;
  const currentSlug = `${slugify(activeTitle || "")}-${propertyId}`;

  const addressChanged =
    formData.country !== currentInitialData?.address?.country ||
    formData.state !== currentInitialData?.address?.state ||
    formData.city !== currentInitialData?.address?.city ||
    formData.area !== currentInitialData?.address?.area ||
    formData.street !== currentInitialData?.address?.street ||
    formData.house_no !== currentInitialData?.address?.house_no ||
    formData.flat_no !== (currentInitialData?.address?.flat_no || "");

  const detailsChanged =
    String(formData.beds) !== String(currentInitialData?.beds || "") ||
    String(formData.baths) !== String(currentInitialData?.baths || "") ||
    String(formData.area_sqft) !== String(currentInitialData?.area_sqft || "");

  const hasUnsavedChanges =
    formData.title !== currentInitialData?.title ||
    formData.description !== currentInitialData?.description ||
    addressChanged ||
    detailsChanged ||
    String(formData.price) !== String(currentInitialData?.price || "") ||
    previewUrl !== currentInitialData?.image_url;

  const isTitleComplete =
    formData.title.trim() !== "" &&
    formData.title !== currentInitialData?.title;

  const isDescriptionComplete =
    formData.description.trim() !== "" &&
    formData.description !== currentInitialData?.description;

  const isAddressComplete =
    formData.country.trim() !== "" &&
    formData.house_no.trim() !== "" &&
    addressChanged;

  const isDetailsComplete =
    formData.beds !== "" && formData.baths !== "" && detailsChanged;

  const isPricingComplete =
    formData.price !== "" &&
    String(formData.price) !== String(currentInitialData?.price || "");

  const isImageComplete =
    previewUrl !== null && previewUrl !== currentInitialData?.image_url;

  const resetImageInput = () => {
    setPreviewUrl(state.formPropertyData.image_url);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleInputChange = (e) => {
    const { type, name, value } = e.target;
    let newValue = value;

    if (type === "number") {
      if (value === "") {
        newValue = "";
      } else {
        const limits = {
          price: /^\d{0,13}(\.\d{0,2})?$/,
          area_sqft: /^\d{0,10}(\.\d{0,4})?$/,
          beds: /^\d{0,10}$/,
          baths: /^\d{0,10}$/,
        };

        if (limits[name] && !limits[name].test(value)) {
          return;
        }

        newValue = value;
      }
    }
    setFormData((prev) => ({ ...prev, [name]: newValue }));
  };

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setLocalImageError("");
      const validTypes = ["image/jpeg", "image/png", "image/jpg"];
      const isInvalidType = !validTypes.includes(file.type);
      const isTooLarge = file.size > 2 * 1024 * 1024;

      if (isInvalidType || isTooLarge) {
        const msg = isInvalidType
          ? "Only JPG, JPEG and PNG images are allowed."
          : "Image size should not exceed 2MB.";

        setLocalImageError(msg);
        return;
      }

      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }

      setPreviewUrl(URL.createObjectURL(file));
      setFormData((prev) => ({ ...prev, property_image: file }));
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
    autoResize(textAreaRef.current);
  }, [formData.description]);

  useEffect(() => {
    const handleResize = () => autoResize(textAreaRef.current);
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  useEffect(() => {
    return () => {
      if (previewUrl?.startsWith("blob:")) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  useEffect(() => {
    if (state.errors && state.errors.image_url) {
      resetImageInput();
    }
  }, [state.errors]);

  useEffect(() => {
    if (state.success) {
      setDisplaySuccess(state.success);
      setLocalImageError("");

      setCurrentInitialData({
        title: formData.title,
        description: formData.description,
        beds: formData.beds,
        baths: formData.baths,
        area_sqft: formData.area_sqft,
        price: formData.price,
        image_url: previewUrl,
        address: {
          country: formData.country,
          state: formData.state,
          city: formData.city,
          area: formData.area,
          street: formData.street,
          house_no: formData.house_no,
          flat_no: formData.flat_no,
        },
      });

      const timer = setTimeout(() => {
        setDisplaySuccess("");
        router.refresh();
      }, 3000);

      return () => clearTimeout(timer);
    }
  }, [state.success, router]);

  return (
    <div className={styles.container}>
      <UpdateAlert hasUnsavedChanges={hasUnsavedChanges} />
      <div className={styles.sidebar}>
        <div className={styles.sidebarContent}>
          <div className={styles.sidebarHeader}>
            <div className={styles.sidebarTitle}>Update a listing</div>
            <div className={styles.sidebarSubtitle}>
              Input property information
            </div>
          </div>

          <div className={styles.checklist}>
            {[
              { label: "Title", check: isTitleComplete },
              { label: "Description", check: isDescriptionComplete },
              { label: "Address", check: isAddressComplete },
              { label: "Details", check: isDetailsComplete },
              { label: "Pricing", check: isPricingComplete },
              { label: "Image", check: isImageComplete },
            ].map((item, idx) => (
              <div key={idx} className={styles.checkItem}>
                <div>
                  <Image
                    src={item.check ? doneIcon : notDoneIcon}
                    alt="status"
                    width={24}
                    height={24}
                    className={styles.icon}
                  />
                </div>
                <div className={styles.label}>{item.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className={styles.formContainer}>
        <Form action={formAction}>
          <div className={styles.section}>
            <div className={styles.sectionTitle}>Title</div>
            <input
              type="text"
              name="title"
              value={formData.title}
              placeholder="Title"
              onChange={handleInputChange}
              className={styles.input}
            />
            {Object.keys(state.errors).length > 0 && state.errors.title && (
              <div className={styles.errorBox}>{state.errors.title}</div>
            )}
          </div>

          <div className={styles.section}>
            <div className={styles.sectionTitle}>Description</div>
            <div className={styles.descContainer}>
              <textarea
                name="description"
                ref={textAreaRef}
                placeholder="Description"
                value={formData.description}
                onChange={handleInputChange}
                className={styles.storedText}
                maxLength={150}
              />
              <div className={styles.charCount}>
                {formData.description.length} / 150
              </div>
            </div>
            {Object.keys(state.errors).length > 0 &&
              state.errors.description && (
                <div className={styles.errorBox}>
                  {state.errors.description}
                </div>
              )}
          </div>

          <div className={styles.section}>
            <div className={styles.sectionTitle}>Address</div>
            <div className={styles.gridThree}>
              <div className={styles.inputContainer}>
                <h1 className={styles.inputTitle}>Country*</h1>
                <input
                  type="text"
                  placeholder="Country"
                  name="country"
                  value={formData.country}
                  onChange={handleInputChange}
                  className={styles.input}
                />
              </div>

              <div className={styles.inputContainer}>
                <h1 className={styles.inputTitle}>State*</h1>
                <input
                  type="text"
                  placeholder="State"
                  name="state"
                  value={formData.state}
                  onChange={handleInputChange}
                  className={styles.input}
                />
              </div>

              <div className={styles.inputContainer}>
                <h1 className={styles.inputTitle}>City*</h1>
                <input
                  type="text"
                  placeholder="City"
                  name="city"
                  value={formData.city}
                  onChange={handleInputChange}
                  className={styles.input}
                />
              </div>

              <div className={styles.inputContainer}>
                <h1 className={styles.inputTitle}>Area*</h1>
                <input
                  type="text"
                  placeholder="Area"
                  name="area"
                  value={formData.area}
                  onChange={handleInputChange}
                  className={styles.input}
                />
              </div>

              <div className={styles.inputContainer}>
                <h1 className={styles.inputTitle}>Street*</h1>
                <input
                  type="text"
                  placeholder="Street"
                  name="street"
                  value={formData.street}
                  onChange={handleInputChange}
                  className={styles.input}
                />
              </div>

              <div className={styles.inputContainer}>
                <h1 className={styles.inputTitle}>House No.*</h1>
                <input
                  type="text"
                  placeholder="House No."
                  name="house_no"
                  value={formData.house_no}
                  onChange={handleInputChange}
                  className={styles.input}
                />
              </div>
            </div>

            <div className={styles.inputContainer}>
              <h1 className={styles.inputTitle}>Flat No. (optional)</h1>
              <input
                type="text"
                placeholder="Flat No."
                name="flat_no"
                value={formData.flat_no}
                onChange={handleInputChange}
                className={styles.input}
              />
            </div>
            {Object.keys(state.errors).length > 0 && state.errors.address && (
              <div className={styles.errorBox}>{state.errors.address}</div>
            )}
          </div>

          <div className={styles.section}>
            <div className={styles.sectionTitle}>Details</div>
            <div className={styles.gridThree}>
              <div className={styles.inputContainer}>
                <h1 className={styles.inputTitle}>Beds*</h1>
                <input
                  type="number"
                  placeholder="Beds"
                  name="beds"
                  value={formData.beds}
                  onChange={handleInputChange}
                  className={styles.input}
                />
                {Object.keys(state.errors).length > 0 && state.errors.beds && (
                  <div className={styles.errorBox}>{state.errors.beds}</div>
                )}
              </div>

              <div className={styles.inputContainer}>
                <h1 className={styles.inputTitle}>Baths*</h1>
                <input
                  type="number"
                  placeholder="Baths"
                  name="baths"
                  value={formData.baths}
                  onChange={handleInputChange}
                  className={styles.input}
                />
                {Object.keys(state.errors).length > 0 && state.errors.baths && (
                  <div className={styles.errorBox}>{state.errors.baths}</div>
                )}
              </div>

              <div className={styles.inputContainer}>
                <h1 className={styles.inputTitle}>Sqft*</h1>
                <input
                  type="number"
                  placeholder="Sqft"
                  name="area_sqft"
                  value={formData.area_sqft}
                  onChange={handleInputChange}
                  className={styles.input}
                />
                {Object.keys(state.errors).length > 0 &&
                  state.errors.area_sqft && (
                    <div className={styles.errorBox}>
                      {state.errors.area_sqft}
                    </div>
                  )}
              </div>
            </div>
          </div>

          <div className={styles.section}>
            <div className={styles.sectionTitle}>Pricing</div>
            <div className={styles.priceInputWrapper}>
              <div className={styles.dollarSign}>$</div>
              <input
                type="number"
                name="price"
                placeholder="0.00"
                value={formData.price}
                onChange={handleInputChange}
                className={styles.priceInput}
              />
            </div>
            {Object.keys(state.errors).length > 0 && state.errors.price && (
              <div className={styles.errorBox}>{state.errors.price}</div>
            )}
          </div>

          <div className={styles.section}>
            <div className={styles.sectionTitle}>Image</div>
            <div
              className={
                previewUrl
                  ? styles.imageUploadBox
                  : styles.singleUploadContainer
              }
            >
              {previewUrl && (
                <div className={styles.imagePreviewContainer}>
                  <Image
                    src={previewUrl}
                    alt="Preview"
                    width={400}
                    height={300}
                    className={styles.imagePreview}
                  />
                </div>
              )}

              <div className={styles.uploadControlSide}>
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleImageChange}
                  name="property_image"
                  accept="image/*"
                  className={styles.imageInput}
                  style={{ display: "none" }}
                  disabled={isPending}
                />
                <div className={styles.uploadLabel}>
                  <div
                    className={styles.uploadIconCircle}
                    onClick={handleIconClick}
                  >
                    <Image
                      src={uploadIcon}
                      alt="Upload"
                      width={30}
                      height={30}
                    />
                  </div>
                  <div className={styles.uploadText}>Choose File to Upload</div>
                  <div className={styles.uploadSubtext}>
                    Maximum Upload Size 2MB
                  </div>
                </div>
              </div>
            </div>
            {localImageError ? (
              <span className={styles.errorBox}>{localImageError}</span>
            ) : Object.keys(state.errors).length > 0 &&
              state.errors.image_url ? (
              <span className={styles.errorText}>{state.errors.image_url}</span>
            ) : null}
          </div>

          {displaySuccess && (
            <div className={styles.successBox}>{displaySuccess}</div>
          )}
          {Object.keys(state.errors).length > 0 && state.errors.general && (
            <div className={styles.errorBox2}>{state.errors.general}</div>
          )}

          <div className={styles.buttonGroup}>
            <div className={styles.cancelProfileButton}>
              <Link
                href={`/properties/${currentSlug}`}
                className={styles.cancelProfileButtonLink}
              >
                Cancel
              </Link>
            </div>
            <FormButton
              type="submit"
              text="Update"
              pendingText="Updating..."
              disabled={isPending}
              className={styles.submitBtn}
            />
          </div>
        </Form>
      </div>
    </div>
  );
}
